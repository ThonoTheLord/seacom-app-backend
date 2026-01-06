from uuid import UUID
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, DateTime, Relationship
from abc import ABC
from datetime import datetime

from app.utils.enums import AccessRequestStatus
from app.utils.funcs import utcnow
from .base import BaseDB

if TYPE_CHECKING:
    from .technician import Technician
    from .site import Site


class BaseAccessRequest(SQLModel, ABC):
    technician_id: UUID = Field(foreign_key="technicians.id")
    site_id: UUID = Field(foreign_key="sites.id")
    description: str = Field(nullable=False, max_length=2000)
    start: datetime = Field(nullable=False, sa_type=DateTime(timezone=True)) # type: ignore
    end: datetime = Field(nullable=False, sa_type=DateTime(timezone=True)) # type: ignore


class AccessRequest(BaseDB, BaseAccessRequest, table=True):
    __tablename__ = "access_requests" # type: ignore

    status: AccessRequestStatus = Field(default=AccessRequestStatus.REQUESTED)
    access_code: str | None = Field(default=None)
    approved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True)) # type: ignore

    technician: 'Technician' = Relationship(back_populates="access_requests")
    site: 'Site' = Relationship(back_populates="access_requests")

    def approve(self, code: str) -> None:
        self.status = AccessRequestStatus.APPROVED
        self.approved_at = utcnow()
        self.access_code = code
        self.touch()
    
    def reject(self) -> None:
        self.status = AccessRequestStatus.REJECTED
        self.touch()


class AccessRequestCreate(BaseAccessRequest): ...


class AccessRequestUpdate(SQLModel):
    description: str | None = Field(default=None, max_length=2000)
    start: datetime | None = Field(default=None)


class AccessRequestResponse(BaseDB, BaseAccessRequest):
    status: AccessRequestStatus = Field(default=AccessRequestStatus.REQUESTED)
    access_code: str | None = Field(default=None)
    technician_name: str = Field(default="")
    technician_id_no: str = Field(default="")
    site_name: str = Field(default="")
