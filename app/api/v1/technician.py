from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import TechnicianCreate, TechnicianUpdate, TechnicianResponse, TechnicianLocationUpdate
from app.services import TechnicianService
from app.services.auth import CurrentUser
from app.database import Session

router = APIRouter(prefix="/technicians", tags=["Technicians"])


@router.post("/", response_model=TechnicianResponse, status_code=201)
def create_technician(
    payload: TechnicianCreate,
    service: TechnicianService,
    session: Session
) -> TechnicianResponse:
    """Create a new technician."""
    return service.create_technician(payload, session)


@router.get("/", response_model=List[TechnicianResponse], status_code=200)
def read_technicians(
    service: TechnicianService,
    session: Session,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[TechnicianResponse]:
    """Get all technicians."""
    return service.read_technicians(session, offset, limit)


# ==================== DISPATCH ENDPOINTS ====================

@router.get("/dispatch/nearest", response_model=List[TechnicianResponse], status_code=200)
def find_nearest_technicians(
    service: TechnicianService,
    session: Session,
    latitude: float = Query(ge=-90, le=90, description="Target latitude"),
    longitude: float = Query(ge=-180, le=180, description="Target longitude"),
    limit: int = Query(default=5, ge=1, le=20, description="Max technicians to return"),
    available_only: bool = Query(default=True, description="Only return available technicians"),
    max_distance_km: float | None = Query(default=None, ge=0, description="Max distance in km"),
) -> List[TechnicianResponse]:
    """
    Find nearest technicians to a location.
    Used for smart dispatch of incidents and tasks.
    Returns technicians sorted by distance with distance_km field populated.
    """
    return service.find_nearest_technicians(
        latitude=latitude,
        longitude=longitude,
        session=session,
        limit=limit,
        available_only=available_only,
        max_distance_km=max_distance_km,
    )


@router.get("/dispatch/nearest-to-site/{site_id}", response_model=List[TechnicianResponse], status_code=200)
def find_nearest_to_site(
    site_id: UUID,
    service: TechnicianService,
    session: Session,
    limit: int = Query(default=5, ge=1, le=20),
    available_only: bool = Query(default=True),
) -> List[TechnicianResponse]:
    """Find nearest technicians to a specific site."""
    return service.find_nearest_to_site(
        site_id=site_id,
        session=session,
        limit=limit,
        available_only=available_only,
    )


@router.get("/dispatch/in-region", response_model=List[TechnicianResponse], status_code=200)
def get_technicians_in_region(
    service: TechnicianService,
    session: Session,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(ge=0.1, le=500, description="Search radius in km"),
    available_only: bool = Query(default=False),
) -> List[TechnicianResponse]:
    """Get all technicians within a radius of a point."""
    return service.get_technicians_in_region(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        session=session,
        available_only=available_only,
    )


@router.get("/monitoring/stale-locations", response_model=List[TechnicianResponse], status_code=200)
def get_stale_locations(
    service: TechnicianService,
    session: Session,
    stale_minutes: int = Query(default=30, ge=5, le=1440),
) -> List[TechnicianResponse]:
    """Get technicians with outdated location data (for NOC monitoring)."""
    return service.get_stale_locations(session, stale_minutes)


# ==================== STANDARD CRUD ====================

@router.get("/{technician_id}", response_model=TechnicianResponse, status_code=200)
def read_technician(
    technician_id: UUID,
    service: TechnicianService,
    session: Session
) -> TechnicianResponse:
    """Get a specific technician by ID."""
    return service.read_technician(technician_id, session)


@router.patch("/{technician_id}", response_model=TechnicianResponse, status_code=200)
def update_technician(
    technician_id: UUID,
    payload: TechnicianUpdate,
    service: TechnicianService,
    session: Session,
) -> TechnicianResponse:
    """Update a technician's profile."""
    return service.update_technician(technician_id, payload, session)


@router.patch("/{technician_id}/location", response_model=TechnicianResponse, status_code=200)
def update_technician_location(
    technician_id: UUID,
    payload: TechnicianLocationUpdate,
    service: TechnicianService,
    session: Session,
) -> TechnicianResponse:
    """
    Update technician's current location.
    Called by mobile app to report real-time position.
    """
    return service.update_location(technician_id, payload, session)


@router.post("/{technician_id}/escalate", status_code=200)
def escalate_technician_issue(
    technician_id: UUID,
    service: TechnicianService,
    session: Session,
    current_user: CurrentUser,
    reason: str = Query(..., description="Reason for escalation"),
    priority: str = Query("HIGH", description="Escalation priority: HIGH, MEDIUM, LOW")
) -> dict:
    """
    Escalate a technician performance or availability issue to management.
    Creates a notification for management users and logs the escalation.
    """
    return service.escalate_technician_issue(
        technician_id=technician_id,
        reason=reason,
        priority=priority,
        escalated_by=current_user.user_id,
        session=session
    )


@router.delete("/{technician_id}", status_code=204)
def delete_technician(
    technician_id: UUID,
    service: TechnicianService,
    session: Session
) -> None:
    """Delete a technician."""
    service.delete_technician(technician_id, session)
