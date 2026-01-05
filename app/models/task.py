from uuid import UUID
from typing import TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, DateTime, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseDB
from app.utils.enums import TaskStatus, TaskType
from app.utils.funcs import utcnow

if TYPE_CHECKING:
    from .site import Site
    from technician import Technician


class BaseTask(SQLModel):
    seacom_ref: str | None = Field(default=None, max_length=100)
    description: str = Field(max_length=2000, nullable=False)
    start_time: datetime = Field(sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    end_time: datetime = Field(sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    task_type: TaskType = Field(nullable=False)
    attachments: dict[str, str] | None = Field(default=None, sa_column=Column(JSONB))
    site_id: UUID = Field(foreign_key="sites.id")
    technician_id: UUID = Field(foreign_key="technicians.id")

    site: 'Site' = Relationship(back_populates="tasks")
    technician: 'Technician' = Relationship(back_populates="tasks")


class Task(BaseDB, BaseTask, table=True):
    status: TaskStatus = Field(default=TaskStatus.PENDING, nullable=False)
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True)) # type: ignore

    def start(self) -> None:
        """"""
        self.status = TaskStatus.STARTED
        self.touch()
    
    def complete(self) -> None:
        """"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = utcnow()
        self.touch()
    
    def fail(self) -> None:
        """"""
        self.status = TaskStatus.FAILED
        self.touch()


class TaskCreate(BaseTask): ...


class TaskUpdate(SQLModel):
    seacom_ref: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000, nullable=False)
    start_time: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    end_time: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=False) # type: ignore
    task_type: TaskType | None = Field(default=None, nullable=False)
    attachments: dict[str, str] | None = Field(default=None, sa_column=Column(JSONB))
    site_id: UUID | None = Field(default=None, foreign_key="sites.id")
    technician_id: UUID | None = Field(default=None, foreign_key="technicians.id")


class TaskResponse(BaseDB, BaseTask):
    site_name: str = Field(default="", description="")
    technician_fullname: str = Field(default="", description="")
    num_attachments: int = Field(default=0, ge=0, description="")
