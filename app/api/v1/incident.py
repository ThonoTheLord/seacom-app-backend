from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import IncidentCreate, IncidentUpdate, IncidentResponse
from app.services import IncidentService, CurrentUser
from app.database import Session
from app.utils.enums import IncidentStatus

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/", response_model=IncidentResponse, status_code=201)
def create_incident(
    payload: IncidentCreate,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> IncidentResponse:
    """"""
    return service.create_incident(payload, session)


@router.get("/", response_model=List[IncidentResponse], status_code=200)
def read_incidents(
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
    technician_id: UUID | None = Query(None),
    status: IncidentStatus | None = Query(None),
    client_id: UUID | None = Query(None, description="Filter by client ID"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[IncidentResponse]:
    """"""
    return service.read_incidents(session, technician_id, status, client_id, offset, limit)


@router.get("/{incident_id}", response_model=IncidentResponse, status_code=200)
def read_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> IncidentResponse:
    """"""
    return service.read_incident(incident_id, session)


@router.patch("/{incident_id}", response_model=IncidentResponse, status_code=200)
def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> IncidentResponse:
    """"""
    return service.update_incident(incident_id, payload, session)


@router.delete("/{incident_id}", status_code=204)
def delete_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> None:
    """"""
    service.delete_incident(incident_id, session)


@router.patch("/{incident_id}/start", response_model=IncidentResponse, status_code=200)
def start_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> IncidentResponse:
    """"""
    return service.start_incident(incident_id, session)


@router.patch("/{incident_id}/resolve", response_model=IncidentResponse, status_code=200)
def resolve_incident(
    incident_id: UUID,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> IncidentResponse:
    """"""
    return service.resolve_incident(incident_id, session)


@router.post("/check-sla", status_code=200)
def check_sla_breaches_endpoint(
    session: Session,
    current_user: CurrentUser,
) -> dict:
    """
    Check for incidents approaching or breaching SLA and send notifications.
    
    This endpoint can be called periodically (e.g., via cron job) to check
    for SLA warnings and breaches, sending notifications to technicians.
    """
    from app.services.sla_checker import check_sla_breaches
    
    warnings, breaches = check_sla_breaches(session)
    
    return {
        "checked_at": __import__("datetime").datetime.utcnow().isoformat(),
        "warnings_sent": len(warnings),
        "breaches_found": len(breaches),
        "warnings": warnings,
        "breaches": breaches
    }


@router.get("/{incident_id}/sla-status", status_code=200)
def get_incident_sla_status(
    incident_id: UUID,
    service: IncidentService,
    session: Session,
    current_user: CurrentUser,
) -> dict:
    """Get the SLA status for a specific incident."""
    from app.services.sla_checker import get_sla_status_for_incident
    from sqlmodel import select
    from app.models import Incident
    
    statement = select(Incident).where(Incident.id == incident_id, Incident.deleted_at.is_(None))
    incident = session.exec(statement).first()
    
    if not incident:
        from app.exceptions.http import NotFoundException
        raise NotFoundException("incident not found")
    
    return get_sla_status_for_incident(incident)

