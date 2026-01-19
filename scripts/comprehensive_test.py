"""Comprehensive integration test script.
Creates 15 users (mix of roles), sends heartbeats via HTTP, checks management listing,
tests logout flow, and reports results.

Run:
  set PYTHONPATH=.&& .venv\Scripts\python.exe scripts\comprehensive_test.py

Notes:
 - This script calls HTTP endpoints; the backend must be running at http://127.0.0.1:8000
 - It uses direct DB writes to create users to avoid requiring a user-creation endpoint.
"""
import time
import json
import os
import requests
from collections import Counter

from sqlmodel import select

from app.database.database import Database
from app.core.settings import app_settings
from app.models.user import User
from app.utils.enums import UserRole
from app.core.security import SecurityUtils


def seed_users():
    # roles distribution: 8 NOC, 3 TECHNICIAN, 2 MANAGER, 2 ADMIN = 15
    roles = [UserRole.NOC]*8 + [UserRole.TECHNICIAN]*3 + [UserRole.MANAGER]*2 + [UserRole.ADMIN]*2
    users = []
    if Database.connection is None:
        Database.connect(app_settings.database_url)
        Database.init()

    with Database.session() as s:
        # create users with unique emails
        idx = 0
        for r in roles:
            idx += 1
            email = f"ci_user_{idx}@example.com"
            existing = s.exec(select(User).where(User.email == email)).first()
            if existing:
                users.append({
                    "id": existing.id,
                    "role": existing.role,
                    "email": existing.email,
                    "name": existing.name,
                    "surname": existing.surname,
                })
                continue
            u = User(name=f"User{idx}", surname=str(r).split('.')[-1], email=email, role=r, password_hash="x")
            s.add(u)
            s.commit()
            s.refresh(u)
            # return simple dicts so caller doesn't rely on a live DB session
            users.append({
                "id": u.id,
                "role": u.role,
                "email": u.email,
                "name": u.name,
                "surname": u.surname,
            })
    return users


def run():
    users = seed_users()
    print(f"Seeded {len(users)} users")
    counts = Counter([u['role'] for u in users])
    print("Role distribution:", {str(k): v for k, v in counts.items()})

    # ensure server is up (allow override via TEST_BASE_URL env var)
    base = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
    try:
        r = requests.get(base + "/openapi.json", timeout=5)
        print("Server openapi ->", r.status_code)
    except Exception as e:
        print("Backend not reachable at http://127.0.0.1:8000 - start server and retry.")
        return

    # send heartbeats for all users
    print("Sending heartbeats for all users...")
    for u in users:
        token = SecurityUtils.create_token(u['id'], u['role'], u['name'], u['surname']).access_token
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.post(base + "/api/v1/sessions/heartbeat", headers=headers, timeout=5)
            if resp.status_code != 200:
                print(f"Heartbeat failed for {u['email']}: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"HTTP heartbeat error for {u['email']}: {e}")

    time.sleep(1)

    # pick a manager to query NOC online
    mgr = next((u for u in users if u['role'] == UserRole.MANAGER), None)
    if not mgr:
        print("No manager found - aborting manager checks")
        return
    mgr_token = SecurityUtils.create_token(mgr['id'], mgr['role'], mgr['name'], mgr['surname']).access_token
    headers_mgr = {"Authorization": f"Bearer {mgr_token}"}

    # call management endpoint
    print("Calling management endpoint /api/v1/dashboard/noc-online")
    r = requests.get(base + "/api/v1/dashboard/noc-online", headers=headers_mgr, params={"cutoff_minutes": 60}, timeout=10)
    print("Status:", r.status_code)
    try:
        data = r.json()
        print(json.dumps(data, indent=2)[:2000])
    except Exception:
        print(r.text[:2000])

    # logout one NOC and check count decreases
    noc_users = [u for u in users if u['role'] == UserRole.NOC]
    if noc_users:
        victim = noc_users[0]
        token_v = SecurityUtils.create_token(victim['id'], victim['role'], victim['name'], victim['surname']).access_token
        headers_v = {"Authorization": f"Bearer {token_v}"}
        print(f"Logging out {victim['email']}")
        resp = requests.post(base + "/api/v1/sessions/logout", headers=headers_v, timeout=5)
        print("Logout status:", resp.status_code)
        time.sleep(0.5)
        r2 = requests.get(base + "/api/v1/dashboard/noc-online", headers=headers_mgr, params={"cutoff_minutes": 60}, timeout=10)
        print("After logout status:", r2.status_code)
        try:
            print(json.dumps(r2.json(), indent=2)[:2000])
        except Exception:
            print(r2.text[:2000])

    print("Comprehensive test completed")


if __name__ == '__main__':
    run()
