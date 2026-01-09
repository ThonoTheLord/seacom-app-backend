from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import NotificationCreate, NotificationResponse
from app.services import NotificationService
from app.database import Session
from app.utils.enums import NotificationPriority

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    payload: NotificationCreate,
    service: NotificationService,
    session: Session
) -> NotificationResponse:
    """"""
    return service.create_notification(payload, session)


@router.get("/", response_model=List[NotificationResponse], status_code=200)
def read_notifications(
    service: NotificationService,
    session: Session,
    priority: NotificationPriority | None = Query(None),
    user_id: UUID | None = Query(None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[NotificationResponse]:
    """"""
    return service.read_notifications(session, priority, user_id, offset, limit)


@router.get("/{notification_id}", response_model=NotificationResponse, status_code=200)
def read_notification(
    notification_id: UUID,
    service: NotificationService,
    session: Session
) -> NotificationResponse:
    """"""
    return service.read_notification(notification_id, session)


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: UUID,
    service: NotificationService,
    session: Session
) -> None:
    """"""
    service.delete_notification(notification_id, session)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, status_code=200)
def mark_as_read(
    notification_id: UUID,
    service: NotificationService,
    session: Session
) -> NotificationResponse:
    """"""
    return service.read(notification_id, session)
