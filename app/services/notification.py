from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.utils.enums import NotificationPriority
from app.models import Notification, NotificationCreate, NotificationResponse, User
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _NotificationService:
    def notification_to_response(self, notification: Notification) -> NotificationResponse:
        return NotificationResponse(
            **notification.model_dump(),
            )

    def create_notification(self, data: NotificationCreate, session: Session) -> NotificationResponse:
        # handle user
        statement = select(User).where(User.id == data.user_id, User.deleted_at.is_(None)) # type: ignore
        user: User | None = session.exec(statement).first()

        if not user:
            raise NotFoundException("user not found")

        notification: Notification = Notification(**data.model_dump(), user=user)
        try:
            session.add(notification)
            session.commit()
            session.refresh(notification)
            return self.notification_to_response(notification)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating notification: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating notification: {e}")

    def read_notification(self, notification_id: UUID, session: Session) -> NotificationResponse:
        notification = self._get_notification(notification_id, session)
        return self.notification_to_response(notification)

    def read_notifications(
        self,
        session: Session,
        priority: NotificationPriority | None = None,
        user_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[NotificationResponse]:
        statement = select(Notification).where(Notification.deleted_at.is_(None))  # type: ignore

        if priority is not None:
            statement = statement.where(Notification.priority == priority)
        if user_id is not None:
            statement = statement.where(Notification.user_id == user_id)

        statement = statement.offset(offset).limit(limit)
        notifications = session.exec(statement).all()
        return [self.notification_to_response(notification) for notification in notifications]

    def delete_notification(self, notification_id: UUID, session: Session) -> None:
        notification = self._get_notification(notification_id, session)
        notification.soft_delete()
        session.commit()

    def _get_notification(self, notification_id: UUID, session: Session) -> Notification:
        statement = select(Notification).where(Notification.id == notification_id, Notification.deleted_at.is_(None))  # type: ignore
        notification: Notification | None = session.exec(statement).first()
        if not notification:
            raise NotFoundException("notification not found")
        return notification


def get_notification_service() -> _NotificationService:
    return _NotificationService()


NotificationService = Annotated[_NotificationService, Depends(get_notification_service)]
