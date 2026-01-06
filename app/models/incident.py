from uuid import UUID
from typing import TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, DateTime, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from abc import ABC

from .base import BaseDB
from app.utils.enums import IncidentStatus
from app.utils.funcs import utcnow

if TYPE_CHECKING:
    from .site import Site
    from technician import Technician


class BaseIncident(SQLModel, ABC):
    seacom_ref: str | None = Field(default=None, max_length=100)
    description: str = Field(max_length=2000, nullable=False)
    start_time: datetime = Field(sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    end_time: datetime = Field(sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    attachments: dict[str, str] | None = Field(default=None, sa_type=JSONB)
    site_id: UUID = Field(foreign_key="sites.id")
    technician_id: UUID = Field(foreign_key="technicians.id")


class Incident(BaseDB, BaseIncident, table=True):
    __tablename__ = "incidents" # type: ignore

    status: IncidentStatus = Field(default=IncidentStatus.OPEN, nullable=False)
    resolved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True)) # type: ignore

    site: 'Site' = Relationship(back_populates="incidents")
    technician: 'Technician' = Relationship(back_populates="incidents")

    def start(self) -> None:
        """"""
        self.status = IncidentStatus.IN_PROGRESS
        self.touch()
    
    def resolve(self) -> None:
        """"""
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = utcnow()
        self.touch()


class IncidentCreate(BaseIncident): ...


class IncidentUpdate(SQLModel):
    seacom_ref: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000, nullable=False)
    start_time: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    end_time: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    attachments: dict[str, str] | None = Field(default=None, sa_column=Column(JSONB))
    site_id: UUID | None = Field(default=None, foreign_key="sites.id")
    technician_id: UUID | None = Field(default=None, foreign_key="technicians.id")


class IncidentResponse(BaseDB, BaseIncident):
    site_name: str = Field(default="", description="")
    technician_fullname: str = Field(default="", description="")
    num_attachments: int = Field(default=0, ge=0, description="")
