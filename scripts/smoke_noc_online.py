"""Smoke test for NOC online feature.
Creates a NOC session and queries the management endpoint using a manager token.
Run: .venv\Scripts\python.exe scripts\smoke_noc_online.py
"""
import time
import json
import requests

from app.database.database import Database
from app.core.settings import app_settings
from app.models.user import User
from sqlmodel import select
from app.utils.enums import UserRole
from app.services.presence import PresenceService
from app.core.security import SecurityUtils


def ensure_user(session, role: UserRole, email: str, name: str, surname: str) -> User:
    u = session.exec(select(User).where(User.email == email)).first()
    if u:
        return u
    user = User(name=name, surname=surname, email=email, role=role, password_hash="smoke-hash")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def main():
    Database.connect(app_settings.database_url)
    Database.init()
    with Database.session() as s:
        noc = ensure_user(s, UserRole.NOC, "smoke-noc@example.com", "Noc", "Operator")
        mgr = ensure_user(s, UserRole.MANAGER, "smoke-mgr@example.com", "Manager", "User")
        noc_id = noc.id
        mgr_id = mgr.id

    # Upsert presence for NOC
    meta = PresenceService.upsert_session(noc_id, str(UserRole.NOC), session_id="smoke-sid-1")
    print("Upserted presence:", json.dumps(meta, indent=2))

    # List via service
    listed = PresenceService.list_active_noc_operators(cutoff_minutes=60)
    print("Listed via service:", json.dumps(listed, indent=2))

    # Create manager token and call API
    token = SecurityUtils.create_token(mgr_id, UserRole.MANAGER, "Manager", "User").access_token
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get("http://127.0.0.1:8000/api/v1/dashboard/noc-online", headers=headers, params={"cutoff_minutes": 60}, timeout=5)
        print("API status:", resp.status_code)
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
    except Exception as e:
        print("HTTP request failed:", e)


if __name__ == "__main__":
    main()
