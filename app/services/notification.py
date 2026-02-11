from dataclasses import dataclass
from typing import Annotated, Iterable, List
from uuid import UUID

from fastapi import Depends
from loguru import logger as LOG
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)
from app.models import Notification, NotificationCreate, NotificationResponse, User
from app.utils.enums import NotificationPriority


@dataclass(frozen=True)
class NotificationTemplate:
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL


class NotificationTemplates:
    @staticmethod
    def _clean(text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.split())

    @staticmethod
    def _preview(text: str | None, limit: int = 110) -> str:
        cleaned = NotificationTemplates._clean(text)
        if not cleaned:
            return "No details provided."
        if len(cleaned) <= limit:
            return cleaned
        return f"{cleaned[:limit - 3].rstrip()}..."

    @staticmethod
    def _label(value: str | object) -> str:
        text = str(value).replace("-", " ").replace("_", " ").strip()
        return text.title()

    @staticmethod
    def task_assigned(site_name: str, description: str | None) -> NotificationTemplate:
        return NotificationTemplate(
            title="Task assigned",
            message=(
                f"You were assigned a task at {site_name}. "
                f"Details: {NotificationTemplates._preview(description)}"
            ),
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def task_started(technician_name: str, site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Task in progress",
            message=f"{technician_name} started work at {site_name}.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def task_completed(technician_name: str, site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Task completed",
            message=(
                f"{technician_name} completed work at {site_name}. "
                "Review the generated report."
            ),
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def task_failed(technician_name: str, site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Task failed",
            message=(
                f"{technician_name} could not complete the task at {site_name}. "
                "Immediate review is required."
            ),
            priority=NotificationPriority.CRITICAL,
        )

    @staticmethod
    def report_auto_created(report_type: str | object, site_name: str) -> NotificationTemplate:
        report_label = NotificationTemplates._label(report_type)
        return NotificationTemplate(
            title="Report ready for update",
            message=(
                f"A {report_label} report was created for {site_name}. "
                "Open it and add your findings."
            ),
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def report_submitted(
        technician_name: str,
        report_type: str | object,
        site_name: str,
    ) -> NotificationTemplate:
        report_label = NotificationTemplates._label(report_type)
        return NotificationTemplate(
            title="New report submitted",
            message=f"{technician_name} submitted a {report_label} report for {site_name}.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def incident_assigned_to_technician(site_name: str, description: str | None) -> NotificationTemplate:
        return NotificationTemplate(
            title="Incident assigned",
            message=(
                f"You were assigned an incident at {site_name}. "
                f"Details: {NotificationTemplates._preview(description)}"
            ),
            priority=NotificationPriority.CRITICAL,
        )

    @staticmethod
    def incident_created_for_noc(
        site_name: str,
        technician_name: str,
        description: str | None,
    ) -> NotificationTemplate:
        return NotificationTemplate(
            title="New incident created",
            message=(
                f"Incident at {site_name} assigned to {technician_name}. "
                f"Details: {NotificationTemplates._preview(description)}"
            ),
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def incident_in_progress(technician_name: str, site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Incident in progress",
            message=f"{technician_name} started working on the incident at {site_name}.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def incident_resolved(technician_name: str, site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Incident resolved",
            message=f"{technician_name} resolved the incident at {site_name}.",
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def access_request_created(
        site_name: str,
        technician_name: str,
        description: str | None,
    ) -> NotificationTemplate:
        return NotificationTemplate(
            title="Access request submitted",
            message=(
                f"{technician_name} requested site access for {site_name}. "
                f"Details: {NotificationTemplates._preview(description)}"
            ),
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def access_request_approved(site_name: str, seacom_ref: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Access request approved",
            message=f"Access to {site_name} was approved. Reference: {seacom_ref}.",
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def access_request_rejected(site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Access request rejected",
            message=f"Access to {site_name} was rejected. Contact NOC for next steps.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def inspection_started(site_name: str, technician_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Routine inspection started",
            message=f"{technician_name} started a generator inspection at {site_name}.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def inspection_completed(site_name: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Routine inspection completed",
            message=f"The generator inspection for {site_name} has been submitted.",
            priority=NotificationPriority.NORMAL,
        )

    @staticmethod
    def sla_warning(site_name: str, priority: str, time_remaining: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="SLA warning",
            message=(
                f"Incident at {site_name} ({priority.upper()} priority) breaches SLA in {time_remaining}. "
                "Start work now."
            ),
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def sla_breached(site_name: str, priority: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="SLA breached",
            message=(
                f"Incident at {site_name} ({priority.upper()} priority) has breached SLA. "
                "Immediate escalation is required."
            ),
            priority=NotificationPriority.CRITICAL,
        )

    @staticmethod
    def technician_escalation(technician_name: str, priority: str, reason: str) -> NotificationTemplate:
        return NotificationTemplate(
            title="Technician escalation",
            message=(
                f"{technician_name} escalation ({priority.upper()}): "
                f"{NotificationTemplates._preview(reason, 180)}"
            ),
            priority=(
                NotificationPriority.HIGH
                if priority.upper() == "HIGH"
                else NotificationPriority.NORMAL
            ),
        )


class _NotificationService:
    def notification_to_response(self, notification: Notification) -> NotificationResponse:
        return NotificationResponse(**notification.model_dump())

    def create_notification(self, data: NotificationCreate, session: Session) -> NotificationResponse:
        statement = select(User).where(User.id == data.user_id, User.deleted_at.is_(None))  # type: ignore
        user: User | None = session.exec(statement).first()

        if not user:
            raise NotFoundException("user not found")

        notification = Notification(**data.model_dump(), user=user)
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

    def create_notification_for_user(
        self,
        user_id: UUID,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        session: Session | None = None,
    ) -> NotificationResponse | None:
        if session is None:
            LOG.warning("Notification skipped for user {} because session was None.", user_id)
            return None

        try:
            notification_data = NotificationCreate(
                user_id=user_id,
                title=title.strip(),
                message=message.strip(),
                priority=priority,
            )
            return self.create_notification(notification_data, session)
        except Exception as exc:
            LOG.warning("Notification creation failed for user {}: {}", user_id, exc)
            return None

    def create_notification_from_template(
        self,
        user_id: UUID,
        template: NotificationTemplate,
        session: Session,
    ) -> NotificationResponse | None:
        return self.create_notification_for_user(
            user_id=user_id,
            title=template.title,
            message=template.message,
            priority=template.priority,
            session=session,
        )

    def create_notifications_from_template(
        self,
        user_ids: Iterable[UUID],
        template: NotificationTemplate,
        session: Session,
    ) -> int:
        sent = 0
        for user_id in user_ids:
            if self.create_notification_from_template(user_id, template, session):
                sent += 1
        return sent

    def read_notification(self, notification_id: UUID, session: Session) -> NotificationResponse:
        notification = self._get_notification(notification_id, session)
        return self.notification_to_response(notification)

    def read_notifications(
        self,
        session: Session,
        priority: NotificationPriority | None = None,
        user_id: UUID | None = None,
        read: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[NotificationResponse]:
        statement = select(Notification).where(Notification.deleted_at.is_(None))  # type: ignore

        if priority is not None:
            statement = statement.where(Notification.priority == priority)
        if user_id is not None:
            statement = statement.where(Notification.user_id == user_id)
        if read is not None:
            statement = statement.where(Notification.read == read)

        statement = statement.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        notifications = session.exec(statement).all()
        return [self.notification_to_response(notification) for notification in notifications]

    def get_unread_count(self, user_id: UUID, session: Session) -> int:
        statement = select(Notification).where(
            Notification.deleted_at.is_(None),  # type: ignore
            Notification.user_id == user_id,
            Notification.read.is_(False),
        )
        return len(session.exec(statement).all())

    def delete_notification(self, notification_id: UUID, session: Session) -> None:
        notification = self._get_notification(notification_id, session)
        notification.soft_delete()
        session.commit()

    def read(self, notification_id: UUID, session: Session) -> NotificationResponse:
        notification = self._get_notification(notification_id, session)
        notification.read = True
        notification.touch()
        try:
            session.commit()
            session.refresh(notification)
            return self.notification_to_response(notification)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error marking notification as read: {e}")

    def mark_all_as_read(self, user_id: UUID, session: Session) -> int:
        statement = select(Notification).where(
            Notification.deleted_at.is_(None),  # type: ignore
            Notification.user_id == user_id,
            Notification.read.is_(False),
        )
        unread_items = session.exec(statement).all()
        if not unread_items:
            return 0

        for notification in unread_items:
            notification.read = True
            notification.touch()

        try:
            session.commit()
            return len(unread_items)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error marking all notifications as read: {e}")

    def _get_notification(self, notification_id: UUID, session: Session) -> Notification:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.deleted_at.is_(None),  # type: ignore
        )
        notification: Notification | None = session.exec(statement).first()
        if not notification:
            raise NotFoundException("notification not found")
        return notification


def get_notification_service() -> _NotificationService:
    return _NotificationService()


NotificationService = Annotated[_NotificationService, Depends(get_notification_service)]
