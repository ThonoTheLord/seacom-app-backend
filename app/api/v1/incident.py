from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import IncidentCreate, IncidentUpdate, IncidentResponse
from app.services import IncidentService
from app.database import Session
from app.utils.enums import IncidentStatus

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/", response_model=IncidentResponse, status_code=201)
def create_incident(
    payload: IncidentCreate,
    service: IncidentService,
    session: Session
) -> IncidentResponse:
    """"""
    return service.create_incident(payload, session)


@router.get("/", response_model=List[IncidentResponse], status_code=200)
def read_incidents(
    service: IncidentService,
    session: Session,
    technician_id: UUID | None = Query(None),
    status: IncidentStatus | None = Query(None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[IncidentResponse]:
    """"""
    return service.read_incidents(session, technician_id, status, offset, limit)


@router.get("/{incident_id}", response_model=IncidentResponse, status_code=200)
def read_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session
) -> IncidentResponse:
    """"""
    return service.read_incident(incident_id, session)


@router.patch("/{incident_id}", response_model=IncidentResponse, status_code=200)
def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    service: IncidentService,
    session: Session,
) -> IncidentResponse:
    """"""
    return service.update_incident(incident_id, payload, session)


@router.delete("/{incident_id}", status_code=204)
def delete_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session
) -> None:
    """"""
    service.delete_incident(incident_id, session)


@router.patch("/{incident_id}/start", response_model=IncidentResponse, status_code=200)
def start_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session
) -> IncidentResponse:
    """"""
    return service.start_incident(incident_id, session)


@router.patch("/{incident_id}/resolve", response_model=IncidentResponse, status_code=200)
def resolve_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session
) -> IncidentResponse:
    """"""
    return service.resolve_incident(incident_id, session)
