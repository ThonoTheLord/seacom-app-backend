from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.utils.enums import TaskType, TaskStatus
from app.models import Task, TaskCreate, TaskUpdate, TaskResponse, Site, Technician
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _TaskService:
    def task_to_response(self, task: Task) -> TaskResponse:
        user = task.technician.user
        return TaskResponse(
            **task.model_dump(),
            site_name=task.site.name,
            technician_fullname=f"{user.name} {user.surname}",
            num_attachments=len(task.attachments or []),
            site_region=task.site.region
            )

    def create_task(self, data: TaskCreate, session: Session) -> TaskResponse:
        # Handle site
        statement = select(Site).where(Site.id == data.site_id, Site.deleted_at.is_(None)) # type: ignore
        site: Site | None = session.exec(statement).first()
        if not site:
            raise NotFoundException("site not found")
        
        # Handle technician
        statement = select(Technician).where(Technician.id == data.technician_id, Technician.deleted_at.is_(None)) # type: ignore
        technician: Technician | None = session.exec(statement).first()
        if not technician:
            raise NotFoundException("technician not found")

        task: Task = Task(**data.model_dump(), site=site, technician=technician)
        try:
            session.add(task)
            session.commit()
            session.refresh(task)
            return self.task_to_response(task)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating task: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating task: {e}")

    def read_task(self, task_id: UUID, session: Session) -> TaskResponse:
        task = self._get_task(task_id, session)
        return self.task_to_response(task)

    def read_tasks(
        self,
        session: Session,
        task_type: TaskType | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[TaskResponse]:
        statement = select(Task).where(Task.deleted_at.is_(None))  # type: ignore

        if task_type is not None:
            statement = statement.where(Task.task_type == task_type)
        if status is not None:
            statement = statement.where(Task.status == status)

        statement = statement.offset(offset).limit(limit)
        tasks = session.exec(statement).all()
        return [self.task_to_response(task) for task in tasks]

    def update_task(
        self, task_id: UUID, data: TaskUpdate, session: Session
    ) -> TaskResponse:
        task = self._get_task(task_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if not update_data:
            return self.task_to_response(task)

        for k, v in update_data.items():
            setattr(task, k, v)

        task.touch()

        try:
            session.commit()
            session.refresh(task)
            return self.task_to_response(task)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating task: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating task: {e}")

    def delete_task(self, task_id: UUID, session: Session) -> None:
        task = self._get_task(task_id, session)
        task.soft_delete()
        session.commit()
    
    def start_task(self, task_id: UUID, session: Session) -> TaskResponse:
        """"""
        task = self._get_task(task_id, session)
        task.start()
        try:
            session.commit()
            session.refresh(task)
            return self.task_to_response(task)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error starting task: {e}")
    
    def complete_task(self, task_id: UUID, session: Session) -> TaskResponse:
        """"""
        task = self._get_task(task_id, session)
        task.complete()
        try:
            session.commit()
            session.refresh(task)
            return self.task_to_response(task)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error completing task: {e}")
    
    def fail_task(self, task_id: UUID, session: Session) -> TaskResponse:
        """"""
        task = self._get_task(task_id, session)
        task.fail()
        try:
            session.commit()
            session.refresh(task)
            return self.task_to_response(task)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error failing task: {e}")

    def _get_task(self, task_id: UUID, session: Session) -> Task:
        statement = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))  # type: ignore
        task: Task | None = session.exec(statement).first()
        if not task:
            raise NotFoundException("task not found")
        return task


def get_task_service() -> _TaskService:
    return _TaskService()


TaskService = Annotated[_TaskService, Depends(get_task_service)]
