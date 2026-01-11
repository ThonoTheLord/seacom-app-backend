from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import AccessRequestCreate, AccessRequestUpdate, AccessRequestResponse
from app.services import AccessRequestService, CurrentUser
from app.database import Session
from app.utils.enums import AccessRequestStatus, UserRole
from app.exceptions.http import ForbiddenException

router = APIRouter(prefix="/access_requests", tags=["Access Requests"])


@router.post("/", response_model=AccessRequestResponse, status_code=201)
def create_access_request(
    payload: AccessRequestCreate,
    service: AccessRequestService,
    session: Session
) -> AccessRequestResponse:
    """"""
    return service.create_access_request(payload, session)


@router.get("/", response_model=List[AccessRequestResponse], status_code=200)
def read_access_requests(
    service: AccessRequestService,
    session: Session,
    status: AccessRequestStatus | None = Query(None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[AccessRequestResponse]:
    """"""
    return service.read_access_requests(session, status, offset, limit)


@router.get("/{access_request_id}", response_model=AccessRequestResponse, status_code=200)
def read_access_request(
    access_request_id: UUID,
    service: AccessRequestService,
    session: Session
) -> AccessRequestResponse:
    """"""
    return service.read_access_request(access_request_id, session)


@router.patch("/{access_request_id}", response_model=AccessRequestResponse, status_code=200)
def update_access_request(
    access_request_id: UUID,
    payload: AccessRequestUpdate,
    service: AccessRequestService,
    session: Session,
) -> AccessRequestResponse:
    """"""
    return service.update_access_request(access_request_id, payload, session)


@router.delete("/{access_request_id}", status_code=204)
def delete_access_request(
    access_request_id: UUID,
    service: AccessRequestService,
    session: Session
) -> None:
    """"""
    service.delete_access_request(access_request_id, session)


@router.patch("/{access_request_id}/approve", status_code=200)
def approve_access_request(
    access_request_id: UUID,
    access_code: str,
    user: CurrentUser,
    service: AccessRequestService,
    session: Session
) -> None:
    """"""
    if user.role not in (UserRole.NOC, UserRole.MANAGER):
        raise ForbiddenException("you are not allowed to perform this action")
    service.approve_access_request(access_request_id, access_code, session)


@router.patch("/{access_request_id}/reject", status_code=200)
def reject_access_request(
    access_request_id: UUID,
    user: CurrentUser,
    service: AccessRequestService,
    session: Session
) -> None:
    """"""
    if user.role not in (UserRole.NOC, UserRole.MANAGER):
        raise ForbiddenException("you are not allowed to perform this action")
    service.reject_access_request(access_request_id, session)
