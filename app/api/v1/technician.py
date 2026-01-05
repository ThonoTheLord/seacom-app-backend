from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import TechnicianCreate, TechnicianUpdate, TechnicianResponse
from app.services import TechnicianService
from app.database import Session

router = APIRouter(prefix="/technicians", tags=["Technicians"])


@router.post("/", response_model=TechnicianResponse, status_code=201)
def create_technician(
    payload: TechnicianCreate,
    service: TechnicianService,
    session: Session
) -> TechnicianResponse:
    """"""
    return service.create_technician(payload, session)


@router.get("/", response_model=List[TechnicianResponse], status_code=200)
def read_technicians(
    service: TechnicianService,
    session: Session,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[TechnicianResponse]:
    """"""
    return service.read_technicians(session, offset, limit)


@router.get("/{technician_id}", response_model=TechnicianResponse, status_code=200)
def read_technician(
    technician_id: UUID,
    service: TechnicianService,
    session: Session
) -> TechnicianResponse:
    """"""
    return service.read_technician(technician_id, session)


@router.patch("/{technician_id}", response_model=TechnicianResponse, status_code=200)
def update_technician(
    technician_id: UUID,
    payload: TechnicianUpdate,
    service: TechnicianService,
    session: Session,
) -> TechnicianResponse:
    """"""
    return service.update_technician(technician_id, payload, session)


@router.delete("/{technician_id}", status_code=204)
def delete_technician(
    technician_id: UUID,
    service: TechnicianService,
    session: Session
) -> None:
    """"""
    service.delete_technician(technician_id, session)
