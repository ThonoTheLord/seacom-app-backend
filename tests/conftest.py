import pytest


@pytest.fixture
def db_session():
    pytest.skip("DB tests disabled while migrating database to Supabase")
