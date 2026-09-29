from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.auth.security import (
    verify_password,
    create_access_token,
    get_current_user,
    AuthenticatedUser,
    canonical_role,
    get_role_permissions,
    ROLE_ADMIN,
    ROLE_SUPERVISOR,
    ROLE_VERIFIER,
    ROLE_OPERATOR,
    ROLE_AUDITOR,
    ROLE_READONLY_API,
    ROLE_PERMISSIONS,
    PERMISSIONS
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


DEMO_PROFILES = {
    "admin": {
        "role": ROLE_ADMIN,
        "full_name": "Smt. Sunita Rao (System Administrator)",
        "email": "admin@bhusetu.gov.in"
    },
    "supervisor": {
        "role": ROLE_SUPERVISOR,
        "full_name": "Shri Arvind Sharma (Sub-Divisional Magistrate / SDO)",
        "email": "supervisor@bhusetu.gov.in"
    },
    "officer_1": {
        "role": ROLE_SUPERVISOR,
        "full_name": "Shri Arvind Sharma (Sub-Divisional Magistrate / SDO)",
        "email": "officer@bhusetu.gov.in"
    },
    "verifier": {
        "role": ROLE_VERIFIER,
        "full_name": "Pooja Deshmukh (Senior Revenue Verifier)",
        "email": "verifier@bhusetu.gov.in"
    },
    "reviewer_1": {
        "role": ROLE_VERIFIER,
        "full_name": "Pooja Deshmukh (Senior Revenue Verifier)",
        "email": "verifier@bhusetu.gov.in"
    },
    "operator": {
        "role": ROLE_OPERATOR,
        "full_name": "Rohan Gaikwad (Patwari / Digitization Operator)",
        "email": "operator@bhusetu.gov.in"
    },
    "auditor": {
        "role": ROLE_AUDITOR,
        "full_name": "K. V. Ramanathan (Vigilance & Audit Officer)",
        "email": "auditor@bhusetu.gov.in"
    },
    "readonly_api": {
        "role": ROLE_READONLY_API,
        "full_name": "Cadastral MIS Integration Client (Automated)",
        "email": "api-client@cadastre.internal"
    }
}


@router.post("/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint returning authentication token, role, and profile."""
    uname = creds.username.lower().strip()

    # 1. Demo users bypass for hackathon demonstration
    if uname in DEMO_PROFILES:
        prof = DEMO_PROFILES[uname]
        token = create_access_token({"sub": uname, "role": prof["role"]})
        perms = list(get_role_permissions(prof["role"]))
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": uname,
                "role": prof["role"],
                "full_name": prof["full_name"],
                "email": prof["email"],
                "permissions": perms
            }
        }

    # 2. Database user check
    user = db.query(User).filter(User.username == uname).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    c_role = canonical_role(user.role)
    token = create_access_token({"sub": user.username, "role": c_role})
    perms = list(get_role_permissions(c_role))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": c_role,
            "full_name": user.full_name,
            "email": user.email,
            "permissions": perms
        }
    }


@router.get("/me")
def get_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Returns currently authenticated user profile and permissions."""
    return {
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "permissions": sorted(list(current_user.permissions))
    }


@router.get("/roles")
def list_roles():
    """Lists available RBAC roles and their associated permissions."""
    return {
        "roles": [
            {
                "id": ROLE_ADMIN,
                "name": "System Administrator",
                "description": "Full access to configure validation rules, review chains, export models, and manage system.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_ADMIN]))
            },
            {
                "id": ROLE_SUPERVISOR,
                "name": "Supervisor / SDO / Tehsildar",
                "description": "Maker-checker double verification approval, task assignment, override certification, audit access.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_SUPERVISOR]))
            },
            {
                "id": ROLE_VERIFIER,
                "name": "Revenue Verifier (Maker)",
                "description": "Examines low-confidence OCR fields, submits corrected values for double verification.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_VERIFIER]))
            },
            {
                "id": ROLE_OPERATOR,
                "name": "Data Operator / Patwari",
                "description": "Uploads land records scans, monitors preprocessing and OCR ingestion pipelines.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_OPERATOR]))
            },
            {
                "id": ROLE_AUDITOR,
                "name": "Vigilance & Compliance Auditor",
                "description": "Read-only access to tamper-evident audit trails and cryptographic hash chain verification.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_AUDITOR]))
            },
            {
                "id": ROLE_READONLY_API,
                "name": "Read-only API Client",
                "description": "External bank/portal integration client with PII-masked query access to certified records.",
                "permissions": sorted(list(ROLE_PERMISSIONS[ROLE_READONLY_API]))
            }
        ],
        "permission_descriptions": PERMISSIONS
    }
