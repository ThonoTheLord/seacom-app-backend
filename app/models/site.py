from sqlmodel import SQLModel, Field

from .base import BaseDB
from app.utils.enums import Region


class BaseSite(SQLModel):
    name: str = Field(description="", nullable=False, max_length=100)
    region: Region = Field(description="", nullable=False)


class Site(BaseDB, BaseSite, table=True):
    __tablename__ = "sites" # type: ignore


class SiteCreate(BaseSite): ...


class SiteUpdate(SQLModel):
    name: str | None = Field(default=None, description="", max_length=100)
    region: Region | None = Field(default=None, description="")


class SiteResponse(BaseDB, BaseSite):
    num_tasks: int = Field(default=0, description="", ge=0)
    num_incidents: int = Field(default=0, description="", ge=0)
    num_reports: int = Field(default=0, description="", ge=0)
