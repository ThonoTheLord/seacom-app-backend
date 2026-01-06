from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.utils.enums import UserRole
from app.models import User, UserCreate, UserUpdate, UserResponse
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)
from app.utils.enums import UserRole, UserStatus
from app.core import SecurityUtils


class _UserService:
    def user_to_response(self, user: User) -> UserResponse:
        return UserResponse(**user.model_dump(exclude={"password_hash"}))

    def create_user(self, data: UserCreate, session: Session) -> UserResponse:
        user = User(
            **data.model_dump(exclude={"password"}), 
            password_hash=SecurityUtils.hash_password(data.password)
            )
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return self.user_to_response(user)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating user: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating user: {e}")

    def read_user(self, user_id: UUID, session: Session) -> UserResponse:
        user = self._get_user(user_id, session)
        return self.user_to_response(user)

    def read_users(
        self,
        session: Session,
        status: UserStatus | None = None,
        role: UserRole | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[UserResponse]:
        statement = select(User).where(User.deleted_at.is_(None))  # type: ignore

        if status is not None:
            statement = statement.where(User.status == status)
        if role is not None:
            statement = statement.where(User.role == role)
        statement = statement.offset(offset).limit(limit)
        users = session.exec(statement).all()
        return [self.user_to_response(user) for user in users]

    def update_user(
        self, user_id: UUID, data: UserUpdate, session: Session
    ) -> UserResponse:
        user = self._get_user(user_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if not update_data:
            return self.user_to_response(user)

        for k, v in update_data.items():
            setattr(user, k, v)

        user.touch()

        try:
            session.commit()
            session.refresh(user)
            return self.user_to_response(user)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating user: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating user: {e}")

    def delete_user(self, user_id: UUID, session: Session) -> None:
        user = self._get_user(user_id, session)
        user.soft_delete()
        session.commit()

    def activate_user(self, user_id: UUID, session: Session) -> UserResponse:
        """"""
        user = self._get_user(user_id, session)
        user.activate()
        session.commit()
        session.refresh(user)
        return self.user_to_response(user)

    def deactivate_user(self, user_id: UUID, session: Session) -> UserResponse:
        """"""
        user = self._get_user(user_id, session)
        user.disable()
        session.commit()
        session.refresh(user)
        return self.user_to_response(user)

    def set_user_role(
        self, user_id: UUID, role: UserRole, session: Session
    ) -> UserResponse:
        """"""
        user = self._get_user(user_id, session)
        user.role = role
        session.commit()
        session.refresh(user)
        return self.user_to_response(user)

    def _get_user(self, user_id: UUID, session: Session) -> User:
        statement = select(User).where(User.id == user_id, User.deleted_at.is_(None))  # type: ignore
        user: User | None = session.exec(statement).first()
        if not user:
            raise NotFoundException("user not found")
        return user


def get_user_service() -> _UserService:
    return _UserService()


UserService = Annotated[_UserService, Depends(get_user_service)]
