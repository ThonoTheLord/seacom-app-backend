from uuid import UUID
from typing import TYPE_CHECKING, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseDB
from app.utils.enums import ReportType, ReportStatus

if TYPE_CHECKING:
    from .technician import Technician
    from .task import Task


class BaseReport(SQLModel):
    report_type: ReportType = Field(nullable=False, description="")
    data: dict[str, Any] = Field(nullable=False, sa_type=JSONB)
    attachments: dict[str, str] | None = Field(default=None, sa_type=JSONB)
    technician_id: UUID = Field(foreign_key="technicians.id")
    task_id: UUID = Field(foreign_key="tasks.id")


class Report(BaseDB, BaseReport, table=True):
    __tablename__ = "reports" # type: ignore

    status: ReportStatus = Field(default=ReportStatus.PENDING, nullable=False)

    technician: 'Technician' = Relationship(back_populates="reports")
    task: 'Task' = Relationship(back_populates="reports")

    def start(self) -> None:
        self.status = ReportStatus.STARTED
        self.touch()
    
    def complete(self) -> None:
        self.status = ReportStatus.COMPLETED
        self.touch()


class ReportCreate(BaseReport): ...


class ReportUpdate(SQLModel):
    data: dict[str, Any] | None = Field(default=None)
    attachments: dict[str, str] | None = Field(default=None)


class ReportResponse(BaseDB, BaseReport):
    status: ReportStatus = Field()
    technician_fullname: str = Field(default="")
