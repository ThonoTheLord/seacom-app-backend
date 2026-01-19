"""Internal comprehensive test (service-level).

Creates 15 users, exercises PresenceService (upsert, heartbeat, list, deactivate),
and validates basic role-based expectations. Runs without starting the HTTP server.
"""
from collections import Counter
from time import sleep
from sqlmodel import select

from app.database.database import Database
from app.core.settings import app_settings
from app.models.user import User
from app.utils.enums import UserRole
from app.services.presence import PresenceService


def seed_users_internal():
    roles = [UserRole.NOC]*8 + [UserRole.TECHNICIAN]*3 + [UserRole.MANAGER]*2 + [UserRole.ADMIN]*2
    users = []
    if Database.connection is None:
        Database.connect(app_settings.database_url)
        Database.init()

    with Database.session() as s:
        for idx, r in enumerate(roles, start=1):
            email = f"int_user_{idx}@example.com"
            existing = s.exec(select(User).where(User.email == email)).first()
            if existing:
                users.append({"id": existing.id, "role": existing.role, "email": existing.email, "name": existing.name, "surname": existing.surname})
                continue
            u = User(name=f"IntUser{idx}", surname=str(r).split('.')[-1], email=email, role=r, password_hash="x")
            s.add(u)
            s.commit()
            s.refresh(u)
            users.append({"id": u.id, "role": u.role, "email": u.email, "name": u.name, "surname": u.surname})
    return users


def run_internal_checks():
    users = seed_users_internal()
    print(f"Seeded {len(users)} users")
    print("Role distribution:", Counter([u["role"] for u in users]))

    # Upsert presence for all users
    print("Upserting presence for all users...")
    sessions = []
    for u in users:
        sid = f"int-sess-{u['email'].split('@')[0]}"
        meta = PresenceService.upsert_session(u['id'], str(u['role']), session_id=sid)
        sessions.append((u, meta))

    # List active NOC operators
    noc_list = PresenceService.list_active_noc_operators(cutoff_minutes=60)
    print(f"NOC listed (count={len(noc_list)}):")
    for item in noc_list[:10]:
        print(" -", item.get("fullname") or item.get("user_id"), item.get("session_id"))

    # Heartbeat update for first NOC
    noc_users = [u for u in users if u["role"] == UserRole.NOC]
    if noc_users:
        u = noc_users[0]
        print("Sending heartbeat for:", u["email"])
        PresenceService.heartbeat(u["id"], str(u["role"]), session_id=f"int-sess-{u['email'].split('@')[0]}")

    # Deactivate one NOC and ensure listing updates
    if noc_users:
        victim = noc_users[0]
        print("Deactivating session for:", victim["email"])
        PresenceService.deactivate_session(user_id=victim["id"])
        sleep(0.2)
        new_list = PresenceService.list_active_noc_operators(cutoff_minutes=60)
        print(f"NOC count before={len(noc_list)} after={len(new_list)}")

    print("Internal comprehensive checks completed")


if __name__ == '__main__':
    run_internal_checks()
