import pytest
from sqlmodel import select

from app.database.database import Database
from app.core.settings import app_settings
from app.models.user import User
from app.utils.enums import UserRole


@pytest.fixture
def db_session():
    # Ensure DB is connected and initialized for tests
    if Database.connection is None:
        Database.connect(app_settings.database_url)
        Database.init()

    with Database.session() as s:
        # Provide compatibility for tests that call `User.select()`
        if not hasattr(User, "select"):
            from sqlmodel import select as _select

            setattr(User, "select", classmethod(lambda cls: _select(cls)))
        # Ensure at least one user exists for presence tests
        existing = s.exec(select(User)).first()
        if not existing:
            u = User(name="Test", surname="User", email="test@example.com", role=UserRole.NOC, password_hash="test-hash")
            s.add(u)
            s.commit()
            s.refresh(u)
        yield s
