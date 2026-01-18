"""
Seed script for the experimental database.
Creates test users for development.

Run with: uv run python scripts/seed_db.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database
from app.core import SecurityUtils, app_settings
from app.models import User
from app.utils.enums import UserRole, UserStatus
from sqlmodel import Session, select


def seed_users():
    """Create test users for development."""
    
    users_to_create = [
        {
            "name": "Admin",
            "surname": "User",
            "email": "admin@seacom-dev.com",
            "password": "admin123",
            "role": UserRole.ADMIN,
        },
        {
            "name": "Manager",
            "surname": "User",
            "email": "manager@seacom-dev.com",
            "password": "manager123",
            "role": UserRole.MANAGER,
        },
        {
            "name": "NOC",
            "surname": "Operator",
            "email": "noc@seacom-dev.com",
            "password": "noc12345",
            "role": UserRole.NOC,
        },
        {
            "name": "John",
            "surname": "Technician",
            "email": "tech@seacom-dev.com",
            "password": "tech1234",
            "role": UserRole.TECHNICIAN,
        },
    ]
    
    with Session(Database.connection) as session:
        for user_data in users_to_create:
            # Check if user already exists
            existing = session.exec(
                select(User).where(User.email == user_data["email"])
            ).first()
            
            if existing:
                print(f"  ⏭️  User {user_data['email']} already exists, skipping...")
                continue
            
            # Create user
            user = User(
                name=user_data["name"],
                surname=user_data["surname"],
                email=user_data["email"],
                password_hash=SecurityUtils.hash_password(user_data["password"]),
                role=user_data["role"],
                status=UserStatus.ACTIVE,
            )
            session.add(user)
            print(f"  ✅ Created {user_data['role'].value}: {user_data['email']} / {user_data['password']}")
        
        session.commit()


def main():
    print("\n🌱 Seeding Experimental Database...")
    print(f"   Database: {app_settings.DB_NAME}")
    print(f"   Host: {app_settings.DB_HOST}:{app_settings.DB_PORT}")
    print()
    
    # Connect to database
    Database.connect(app_settings.database_url)
    
    print("👤 Creating test users...")
    seed_users()
    
    print()
    print("✅ Seeding complete!")
    print()
    print("📋 Test Credentials:")
    print("   ┌─────────────────────────────────────────────────────┐")
    print("   │ Role       │ Email                   │ Password    │")
    print("   ├─────────────────────────────────────────────────────┤")
    print("   │ Admin      │ admin@seacom-dev.com    │ admin123    │")
    print("   │ Manager    │ manager@seacom-dev.com  │ manager123  │")
    print("   │ NOC        │ noc@seacom-dev.com      │ noc12345    │")
    print("   │ Technician │ tech@seacom-dev.com     │ tech1234    │")
    print("   └─────────────────────────────────────────────────────┘")
    print()
    
    Database.disconnect()


if __name__ == "__main__":
    main()
