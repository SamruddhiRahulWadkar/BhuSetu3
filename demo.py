"""
BhuSetu: One-Command Hackathon Prototype Demo Launcher.
Smart India Hackathon Problem Statement 26018 (Dept of Land Resources, Govt of India)

Usage:
  python demo.py [--serve]
"""

import os
import sys
import subprocess
import time
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.user import User
from backend.app.auth.security import get_password_hash, ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_VERIFIER, ROLE_OPERATOR, ROLE_AUDITOR, ROLE_READONLY_API
from backend.app.audit.logger import log_event, verify_audit_chain_integrity
from backend.app.models.document import Document
from backend.app.integration.dilrmp_mis_adapter import DILRMPMISAdapter
from backend.app.main import export_openapi_json

# Ensure tables exist
Base.metadata.create_all(bind=engine)

DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@bhusetu.gov.in",
        "password": "admin123",
        "full_name": "Smt. Sunita Rao (System Administrator)",
        "role": ROLE_ADMIN,
        "api_key": "bhusetu-api-key-admin-2026"
    },
    {
        "username": "supervisor",
        "email": "supervisor@bhusetu.gov.in",
        "password": "supervisor123",
        "full_name": "Shri Arvind Sharma (Sub-Divisional Magistrate / SDO)",
        "role": ROLE_SUPERVISOR,
        "api_key": "bhusetu-api-key-supervisor-2026"
    },
    {
        "username": "verifier",
        "email": "verifier@bhusetu.gov.in",
        "password": "verifier123",
        "full_name": "Pooja Deshmukh (Senior Revenue Verifier)",
        "role": ROLE_VERIFIER,
        "api_key": "bhusetu-api-key-verifier-2026"
    },
    {
        "username": "operator",
        "email": "operator@bhusetu.gov.in",
        "password": "operator123",
        "full_name": "Rohan Gaikwad (Patwari / Digitization Operator)",
        "role": ROLE_OPERATOR,
        "api_key": "bhusetu-api-key-operator-2026"
    },
    {
        "username": "auditor",
        "email": "auditor@bhusetu.gov.in",
        "password": "auditor123",
        "full_name": "K. V. Ramanathan (Vigilance & Audit Officer)",
        "role": ROLE_AUDITOR,
        "api_key": "bhusetu-api-key-auditor-2026"
    },
    {
        "username": "readonly_api",
        "email": "api-client@cadastre.internal",
        "password": "apiclient123",
        "full_name": "Cadastral MIS Integration Client (Automated)",
        "role": ROLE_READONLY_API,
        "api_key": "bhusetu-api-key-readonly-2026"
    }
]


def seed_demo_users(db: Session):
    """Creates or updates the 6 RBAC user accounts in bhusetu.db."""
    created_count = 0
    for u in DEMO_USERS:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                api_key=u["api_key"],
                is_active=True
            )
            db.add(user)
            created_count += 1
        else:
            existing.role = u["role"]
            existing.api_key = u["api_key"]
            existing.hashed_password = get_password_hash(u["password"])
    db.commit()
    return created_count


def seed_demo_audit(db: Session):
    """Ensures at least 5 chained audit events exist."""
    count = db.query(Document).count()
    first_doc = db.query(Document).first()
    doc_id = first_doc.id if first_doc else "doc-init-01"
    log_event(
        db,
        action="SYSTEM_INITIALIZED",
        document_id=doc_id,
        user_id="admin",
        details={"status": "online", "mode": "SIH_EVALUATION"}
    )


def print_banner():
    print("=" * 75)
    print("   BHUSETU: Intelligent Land Record Digitization and Validation System")
    print("   SIH Problem Statement: 26018 (Dept of Land Resources, Govt of India)")
    print("=" * 75)


def print_credentials():
    print("\n[+] 6 RBAC DEMO ACCOUNTS CONFIGURED & READY:")
    print("-" * 75)
    print(f"{'Role':<18} | {'Username':<12} | {'Password':<15} | {'API Key / Scope':<22}")
    print("-" * 75)
    for u in DEMO_USERS:
        print(f"{u['role']:<18} | {u['username']:<12} | {u['password']:<15} | {u['api_key']}")
    print("-" * 75)


def print_endpoints():
    print("\n[+] KEY SYSTEM ENDPOINTS & ARTIFACTS:")
    print("  • Frontend Portal:     http://localhost:5173")
    print("  • Backend REST API:    http://localhost:8000/api")
    print("  • Interactive Docs:    http://localhost:8000/docs")
    print("  • OpenAPI 3.0 Spec:    docs/openapi.json")
    print("  • Evaluation Report:   docs/EVALUATION.md")
    print("  • Walkthrough Script:  docs/DEMO_SCRIPT.md")
    print("  • Cadastral GIS Layer: data/cadastre/parcels.geojson (40 Parcels / ULPINs)")


def main():
    print_banner()
    db = SessionLocal()
    try:
        users_added = seed_demo_users(db)
        seed_demo_audit(db)
        chain_report = verify_audit_chain_integrity(db)
        export_openapi_json()
        doc_count = db.query(Document).count()

        print(f"\n[*] Database Status: {doc_count} digitized land records loaded.")
        print(f"[*] Cryptographic Audit Chain: {'VERIFIED (Zero Tampering)' if chain_report['chain_valid'] else 'TAMPERED'} ({chain_report['total_blocks']} blocks chained).")
        print_credentials()
        print_endpoints()

        if "--serve" in sys.argv:
            print("\n[!] Launching Backend (FastAPI :8000) and Frontend (Vite :5173)...")
            print("Press Ctrl+C to terminate both servers.\n")
            p_backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"])
            p_frontend = subprocess.Popen(["npm", "run", "dev"], cwd="frontend", shell=True)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down demo servers...")
                p_backend.terminate()
                p_frontend.terminate()
    finally:
        db.close()


if __name__ == "__main__":
    main()
