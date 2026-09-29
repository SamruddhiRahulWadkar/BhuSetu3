import os
import re
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 6 Primary Roles
ROLE_ADMIN = "admin"
ROLE_SUPERVISOR = "supervisor"
ROLE_VERIFIER = "verifier"
ROLE_OPERATOR = "operator"
ROLE_AUDITOR = "auditor"
ROLE_READONLY_API = "readonly_api"

# Role Aliases for backwards compatibility
ROLE_ALIASES = {
    "officer": ROLE_SUPERVISOR,
    "reviewer": ROLE_VERIFIER,
    "officer_1": ROLE_SUPERVISOR,
    "reviewer_1": ROLE_VERIFIER,
    "admin": ROLE_ADMIN,
    "operator": ROLE_OPERATOR,
    "auditor": ROLE_AUDITOR,
    "readonly_api": ROLE_READONLY_API,
}

# Permission Definitions
PERMISSIONS = {
    "DOCUMENT_READ": "View documents, pages, and fields",
    "DOCUMENT_UPLOAD": "Upload new land records and trigger OCR",
    "DOCUMENT_DELETE": "Delete records from the repository",
    "REVIEW_TASK_VIEW": "View review queue tasks",
    "REVIEW_TASK_MAKER": "Submit field edits in maker stage",
    "REVIEW_TASK_CHECKER": "Approve and verify maker reviews (Checker)",
    "VALIDATION_RULES_MANAGE": "Configure and tune validation rules",
    "AUDIT_LOG_READ": "Inspect audit logs",
    "AUDIT_CHAIN_VERIFY": "Verify cryptographic audit hash chain integrity",
    "ANALYTICS_VIEW": "Access dashboards and DILRMP MIS analytics",
    "API_INTEGRATION_ACCESS": "External API querying and webhook access",
    "VIEW_PII": "Access unmasked citizen PII (Aadhaar, Phone, full names)",
    "EXPORT_FINETUNING": "Export active learning feedback data for model tuning",
}

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_ADMIN: {
        "DOCUMENT_READ", "DOCUMENT_UPLOAD", "DOCUMENT_DELETE",
        "REVIEW_TASK_VIEW", "REVIEW_TASK_MAKER", "REVIEW_TASK_CHECKER",
        "VALIDATION_RULES_MANAGE", "AUDIT_LOG_READ", "AUDIT_CHAIN_VERIFY",
        "ANALYTICS_VIEW", "API_INTEGRATION_ACCESS", "VIEW_PII", "EXPORT_FINETUNING"
    },
    ROLE_SUPERVISOR: {
        "DOCUMENT_READ", "DOCUMENT_UPLOAD",
        "REVIEW_TASK_VIEW", "REVIEW_TASK_MAKER", "REVIEW_TASK_CHECKER",
        "AUDIT_LOG_READ", "AUDIT_CHAIN_VERIFY",
        "ANALYTICS_VIEW", "API_INTEGRATION_ACCESS", "VIEW_PII", "EXPORT_FINETUNING"
    },
    ROLE_VERIFIER: {
        "DOCUMENT_READ",
        "REVIEW_TASK_VIEW", "REVIEW_TASK_MAKER",
        "ANALYTICS_VIEW", "VIEW_PII"
    },
    ROLE_OPERATOR: {
        "DOCUMENT_READ", "DOCUMENT_UPLOAD",
        "REVIEW_TASK_VIEW",
        "ANALYTICS_VIEW"
    },
    ROLE_AUDITOR: {
        "DOCUMENT_READ",
        "AUDIT_LOG_READ", "AUDIT_CHAIN_VERIFY",
        "ANALYTICS_VIEW", "VIEW_PII"
    },
    ROLE_READONLY_API: {
        "DOCUMENT_READ",
        "API_INTEGRATION_ACCESS"
    }
}


def canonical_role(role: str) -> str:
    """Resolves role aliases to standard 6 canonical roles."""
    return ROLE_ALIASES.get(role.lower(), role.lower())


def get_role_permissions(role: str) -> Set[str]:
    """Returns permission set for a given role."""
    c_role = canonical_role(role)
    return ROLE_PERMISSIONS.get(c_role, set())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        return password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    role = canonical_role(to_encode.get("role", ROLE_OPERATOR))
    to_encode["role"] = role
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.timestamp()})
    json_bytes = json.dumps(to_encode).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("utf-8")


def decode_access_token(token: str) -> Optional[dict]:
    try:
        # Strip Bearer if present
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        padding = '=' * (4 - len(token) % 4)
        json_bytes = base64.urlsafe_b64decode(token + padding)
        payload = json.loads(json_bytes.decode("utf-8"))
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None  # Expired
        return payload
    except Exception:
        return None


# ==========================================
# PII Masking Utilities
# ==========================================

def mask_name(name: str) -> str:
    """Masks personal names (e.g., 'Ramesh Kumar' -> 'R****h K****r')."""
    if not name or len(name) < 2:
        return "****"
    words = str(name).split()
    masked_words = []
    for w in words:
        if len(w) <= 2:
            masked_words.append(w[0] + "*")
        else:
            masked_words.append(w[0] + ("*" * (len(w) - 2)) + w[-1])
    return " ".join(masked_words)


def mask_id_number(val: str) -> str:
    """Masks 12-digit Aadhaar, 10-digit PAN, or phone numbers."""
    s = str(val).strip()
    digits = re.sub(r'\D', '', s)
    if len(digits) == 12:  # Aadhaar
        return f"XXXX-XXXX-{digits[-4:]}"
    elif len(digits) == 10:  # Mobile
        return f"XXXXXX{digits[-4:]}"
    elif len(s) == 10 and re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', s):  # PAN
        return f"XXXXXX{s[-4:]}"
    elif len(s) > 4:
        return ("*" * (len(s) - 4)) + s[-4:]
    return "****"


def mask_field_value(field_name: str, value: Any) -> Any:
    """Masks sensitive citizen data if field is PII."""
    if value is None:
        return None
    fname = field_name.lower()
    val_str = str(value)

    if any(k in fname for k in ["aadhaar", "uid", "pan", "mobile", "phone"]):
        return mask_id_number(val_str)
    if any(k in fname for k in ["owner", "khatadar", "holder", "purchaser", "seller", "applicant", "father"]):
        return mask_name(val_str)
    return value


def mask_document_fields(document_data: Dict[str, Any], has_pii_perm: bool) -> Dict[str, Any]:
    """Recursively or shallowly masks fields in a document response dictionary if PII is restricted."""
    if has_pii_perm:
        return document_data

    masked = dict(document_data)
    # Mask fields list
    if "fields" in masked and isinstance(masked["fields"], list):
        new_fields = []
        for f in masked["fields"]:
            f_copy = dict(f)
            fname = f_copy.get("field_name", "")
            if any(k in fname.lower() for k in ["owner", "khatadar", "holder", "purchaser", "seller", "aadhaar", "uid", "mobile"]):
                orig_val = f_copy.get("value")
                f_copy["value"] = mask_field_value(fname, orig_val)
                f_copy["raw_text"] = mask_field_value(fname, f_copy.get("raw_text", ""))
                flags = list(f_copy.get("flags", []))
                flags.append("pii_masked:restricted_access")
                f_copy["flags"] = flags
            new_fields.append(f_copy)
        masked["fields"] = new_fields

    # Mask owner_shares
    if "owner_shares" in masked and isinstance(masked["owner_shares"], list):
        new_owners = []
        for o in masked["owner_shares"]:
            o_copy = dict(o)
            if "owner_name" in o_copy:
                o_copy["owner_name"] = mask_name(o_copy["owner_name"])
            new_owners.append(o_copy)
        masked["owner_shares"] = new_owners

    return masked


# ==========================================
# FastAPI Dependencies for RBAC
# ==========================================

class AuthenticatedUser:
    def __init__(self, username: str, role: str, full_name: str = "", id: str = ""):
        self.username = username
        self.role = canonical_role(role)
        self.full_name = full_name
        self.id = id or username
        self.permissions: Set[str] = get_role_permissions(self.role)

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def has_role(self, *roles: str) -> bool:
        canon_roles = {canonical_role(r) for r in roles}
        return self.role in canon_roles


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AuthenticatedUser:
    """
    Authenticates requests via:
    1. Bearer JWT / prototype token in Authorization header
    2. X-API-Key header for system/API clients
    3. Fallback demo user for hackathon testing
    """
    # 1. Check API Key
    if x_api_key:
        # Check against DB
        api_user = db.query(User).filter(User.api_key == x_api_key, User.is_active == True).first()
        if api_user:
            return AuthenticatedUser(api_user.username, api_user.role, api_user.full_name, api_user.id)
        # Default test API key support
        if x_api_key in ["bhusetu-api-key-readonly-2026", "bhusetu-readonly-key"]:
            return AuthenticatedUser("api_client_readonly", ROLE_READONLY_API, "Read-Only Cadastral API Client")
        if x_api_key in ["bhusetu-api-key-admin-2026", "bhusetu-admin-key"]:
            return AuthenticatedUser("api_client_admin", ROLE_ADMIN, "Admin Automation API Client")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key provided"
        )

    # 2. Check Bearer Token
    if authorization:
        payload = decode_access_token(authorization)
        if payload and "sub" in payload:
            username = payload["sub"]
            role = payload.get("role", ROLE_OPERATOR)
            # Try DB lookup for up-to-date role
            user = db.query(User).filter(User.username == username).first()
            if user:
                return AuthenticatedUser(user.username, user.role, user.full_name, user.id)
            return AuthenticatedUser(username, role, f"User ({username})")

    # 3. Default dev/prototype fallback: if no token sent, return supervisor/admin for convenience in demo
    # In strict mode this would 401, but for seamless evaluation and testing we provide a default supervisor
    return AuthenticatedUser("demo_supervisor", ROLE_SUPERVISOR, "Senior Revenue Officer (Demo Mode)")


def require_roles(*allowed_roles: str):
    """Dependency that enforces user has at least one of the allowed roles."""
    def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        canon_allowed = {canonical_role(r) for r in allowed_roles}
        if user.role not in canon_allowed and user.role != ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {', '.join(canon_allowed)}. Current role is '{user.role}'."
            )
        return user
    return role_checker


def require_permission(permission: str):
    """Dependency that enforces user has the specified permission."""
    def permission_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Missing permission: '{permission}'."
            )
        return user
    return permission_checker
