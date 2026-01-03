from sqlmodel import SQLModel, Session as _Session, create_engine
from sqlalchemy import Engine
from loguru import logger as LOG
from typing import Generator, List, Annotated
from fastapi import Depends

from app.core.settings import app_settings


class Database:
    """"""

    connection: Engine | None = create_engine(app_settings.database_url)

    @classmethod
    def connect(cls, url: str) -> None:
        """"""
        if cls.connection:
            LOG.warning(
                "Database is already connected. Disconnecting and reconnecting..."
            )
            cls.disconnect()
        try:
            cls.connection = create_engine(url)
            LOG.debug(f"Connected to {cls.connection.url.database} database.")
        except Exception as e:
            message: str = f"Failed to connect to the database: {e}"
            LOG.critical(message)
            raise RuntimeError(message)

    @classmethod
    def disconnect(cls) -> None:
        """"""
        if not cls.connection:
            LOG.warning("Cannot disconnect from the database. Connect first.")
            return
        try:
            db_name: str | None = cls.connection.url.database
            cls.connection.dispose()
            cls.connection = None
            LOG.debug(f"Disconnected from {db_name} database.")
        except Exception as e:
            message: str = f"Failed to disconnect from the database: {e}"
            LOG.exception(message)
            raise RuntimeError(message)

    @classmethod
    def init(cls) -> None:
        """"""
        if not cls.connection:
            LOG.warning("Cannot initialize the database. Connect first.")
            return
        try:
            SQLModel.metadata.create_all(cls.connection)
            table_names: List[str] = [key for key in SQLModel.metadata.tables.keys()]
            LOG.debug(
                f"Initialized {cls.connection.url.database} database and created tables: {', '.join(table_names)}"
            )
        except Exception as e:
            message: str = (
                f"Failed to initialize {cls.connection.url.database} database: {e}"
            )
            LOG.error(message)

    @classmethod
    def get_session(cls) -> Generator[_Session]:
        """"""
        if not cls.connection:
            LOG.critical("Cannot get session. Database is not connected.")
            raise RuntimeError("Cannot get session. Database is not connected.")
        with _Session(cls.connection) as session:
            yield session


Session = Annotated[_Session, Depends(Database.get_session)]
