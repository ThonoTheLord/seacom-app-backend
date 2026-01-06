from fastapi import APIRouter, Query
from typing import List
from uuid import UUID

from app.models import TaskCreate, TaskUpdate, TaskResponse
from app.services import TaskService
from app.database import Session
from app.utils.enums import TaskStatus, TaskType

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(
    payload: TaskCreate,
    service: TaskService,
    session: Session
) -> TaskResponse:
    """"""
    return service.create_task(payload, session)


@router.get("/", response_model=List[TaskResponse], status_code=200)
def read_tasks(
    service: TaskService,
    session: Session,
    task_type: TaskType | None = Query(None),
    status: TaskStatus | None = Query(None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000)
) -> List[TaskResponse]:
    """"""
    return service.read_tasks(session, task_type, status, offset, limit)


@router.get("/{task_id}", response_model=TaskResponse, status_code=200)
def read_task(
    task_id: UUID,
    service: TaskService,
    session: Session
) -> TaskResponse:
    """"""
    return service.read_task(task_id, session)


@router.patch("/{task_id}", response_model=TaskResponse, status_code=200)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    service: TaskService,
    session: Session,
) -> TaskResponse:
    """"""
    return service.update_task(task_id, payload, session)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: UUID,
    service: TaskService,
    session: Session
) -> None:
    """"""
    service.delete_task(task_id, session)


@router.patch("/{task_id}/start", response_model=TaskResponse, status_code=200)
def start_task(
    task_id: UUID,
    service: TaskService,
    session: Session
) -> TaskResponse:
    """"""
    return service.start_task(task_id, session)


@router.patch("/{task_id}/complete", response_model=TaskResponse, status_code=200)
def complete_task(
    task_id: UUID,
    service: TaskService,
    session: Session
) -> TaskResponse:
    """"""
    return service.complete_task(task_id, session)


@router.patch("/{task_id}/fail", response_model=TaskResponse, status_code=200)
def fail_task(
    task_id: UUID,
    service: TaskService,
    session: Session
) -> TaskResponse:
    """"""
    return service.fail_task(task_id, session)
