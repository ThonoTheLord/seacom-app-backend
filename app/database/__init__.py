from .database import Session, Database

# Expose a dependency-compatible get_session at package level
# so other modules can import it as `from app.database import get_session`.
get_session = Database.get_session

__all__ = ["Database", "Session", "get_session"]
