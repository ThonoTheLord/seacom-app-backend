from sqlmodel import SQLModel, Index, Field
from abc import ABC
from pydantic import EmailStr

from .base import BaseDB
from app.utils.enums import UserRole, UserStatus


class BaseUser(SQLModel, ABC):
    """"""

    name: str = Field(
        max_length=100,
        nullable=False,
        description="The first name of the user",
        schema_extra={"examples": {"Moses", "Bongani"}},
    )
    surname: str = Field(
        max_length=100,
        nullable=False,
        description="The last name of the user",
        schema_extra={"examples": {"Kubeka", "Smith"}},
    )
    email: EmailStr = Field(nullable=False, index=True, schema_extra={"examples": {"moses@samotelecoms.co.za"}})
    role: UserRole = Field(description="The role of the user in the system")


class User(BaseDB, BaseUser, table=True):
    """"""

    __tablename__ = "users"  # type: ignore
    __table_args__ = (
        Index(
            "uq_active_users",
            "email",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    password_hash: str = Field(nullable=False)
    status: UserStatus = Field(default=UserStatus.ACTIVE, nullable=False, index=True)

    def activate(self) -> None:
        """"""
        self.status = UserStatus.ACTIVE

    def disable(self) -> None:
        """"""
        self.status = UserStatus.DISABLED
    
    def is_active(self) -> bool:
        """"""
        return self.status == UserStatus.ACTIVE


class UserCreate(BaseUser):
    """"""

    password: str = Field(min_length=8, max_length=16)


class UserUpdate(SQLModel):
    """"""

    name: str | None = Field(
        default=None,
        max_length=100,
        nullable=False,
        description="The first name of the user",
        schema_extra={"examples": {"Moses", "Bongani"}},
    )
    surname: str | None = Field(
        default=None,
        max_length=100,
        nullable=False,
        description="The last name of the user",
        schema_extra={"examples": {"Kubeka", "Smith"}},
    )
    email: EmailStr | None = None


class UserRoleUpdate(SQLModel):
    """"""

    new_role: UserRole


class UserStatusUpdate(SQLModel):
    """"""

    new_status: UserStatus


class UserResponse(BaseDB, BaseUser):
    """"""

    ...
