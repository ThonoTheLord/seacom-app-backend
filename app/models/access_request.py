from uuid import UUID
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, DateTime, Relationship
from abc import ABC
from datetime import datetime

from app.utils.enums import AccessRequestStatus
from .base import BaseDB

if TYPE_CHECKING:
    from .technician import Technician


class BaseAccessRequest(SQLModel, ABC):
    technician_id: UUID = Field(foreign_key="technicians.id")
    site_id: UUID = Field(foreign_key="sites.id")
    description: str = Field(nullable=False, max_length=2000)
    start: datetime = Field(nullable=False, sa_type=DateTime(timezone=True)) # type: ignore
    end: datetime = Field(nullable=False, sa_type=DateTime(timezone=True)) # type: ignore


class AccessRequest(BaseDB, BaseAccessRequest, table=True):
    __tablename__ = "access_requests" # type: ignore

    status: AccessRequestStatus = Field(default=AccessRequestStatus.REQUESTED)

    technician: 'Technician' = Relationship(back_populates="access_requests")


class AccessRequestCreate(BaseAccessRequest): ...


class AccessRequestUpdate(SQLModel):
    description: str | None = Field(default=None, max_length=2000)
    start: datetime | None = Field(default=None)


class AccessRequestResponse(BaseDB, BaseAccessRequest):
    status: AccessRequestStatus = Field(default=AccessRequestStatus.REQUESTED)
    technician_name: str = Field(default="")
    technician_id_no: str = Field(default="")
    site_name: str = Field(default="")
