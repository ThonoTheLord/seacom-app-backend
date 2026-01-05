from uuid import UUID
from pydantic import StringConstraints
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from abc import ABC

from .base import BaseDB

SA_ID = Annotated[str, StringConstraints(
    strip_whitespace=True,
    min_length=13,
    max_length=13
)]

if TYPE_CHECKING:
    from .user import User


class BaseTechnician(SQLModel, ABC):
    phone: str = Field(nullable=False, max_length=13, min_length=10, description="", unique=True)
    id_no: SA_ID = Field(nullable=False, unique=True, description="")
    user_id: UUID = Field(nullable=False, foreign_key="users.id")


class Technician(BaseDB, BaseTechnician, table=True):
    __tablename__ = "technicians" # type: ignore

    user: 'User' = Relationship()


class TechnicianCreate(BaseTechnician): ...


class TechnicianUpdate(SQLModel):
    phone: str | None = Field(default=None, max_length=13, min_length=10, description="")


class TechnicianResponse(BaseDB, BaseTechnician):
    fullname: str = Field(default="", description="")

