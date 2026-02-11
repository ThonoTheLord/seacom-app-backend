from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from loguru import logger as LOG

from app.utils.enums import TaskType, TaskStatus, ReportType, ReportStatus, UserRole
from app.models import Task, TaskCreate, TaskUpdate, TaskResponse, Site, Technician, User, Report
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _TaskService:
    _REPORT_TYPE_ALIASES: dict[str, str] = {
        "rhs": ReportType.GENERAL,
        "corrective": ReportType.GENERAL,
        "remote-hand-support": ReportType.GENERAL,
        "routine-maintenance": ReportType.ROUTINE_DRIVE,
    }

    def task_to_response(self, task: Task) -> TaskResponse:
        user = task.technician.user
        return TaskResponse(
            **task.model_dump(),
            site_name=task.site.name,
            technician_fullname=f"{user.name} {user.surname}",
            num_attachments=len(task.attachments or []),
            site_region=task.site.region
            )

    def _resolve_report_type(self, task: Task) -> ReportType:
        """Resolve report type from task.report_type with legacy alias support."""
        raw_report_type = (task.report_type or "").strip().lower()
        valid_values = {item.value for item in ReportType}

        if raw_report_type:
            if raw_report_type in valid_values:
                return ReportType(raw_report_type)

            alias = self._REPORT_TYPE_ALIASES.get(raw_report_type)
            if alias in valid_values:
                return ReportType(alias)

        if task.task_type == TaskType.ROUTINE_MAINTENANCE:
            return ReportType.ROUTINE_DRIVE
        return ReportType.GENERAL

    def _get_active_report_for_task(self, task_id: UUID, session: Session) -> Report | None:
        statement = (
            select(Report)
            .where(
                Report.task_id == task_id,
                Report.deleted_at.is_(None),
            )
            .order_by(
                Report.updated_at.desc().nullslast(),
                Report.created_at.desc().nullslast(),
                Report.id.desc(),
            )
        )
        return session.exec(statement).first()

    def _ensure_auto_report_for_task(
        self,
        task: Task,
        session: Session,
        source: str,
    ) -> tuple[Report, bool]:
        existing = self._get_active_report_for_task(task.id, session)
        if existing:
            return existing, False

        resolved_report_type = self._resolve_report_type(task)
        site_name = task.site.name if task.site else "Unknown Site"

        report = Report(
            task_id=task.id,
            technician_id=task.technician_id,
            report_type=resolved_report_type,
            status=ReportStatus.PENDING,
            service_provider="SEACOM",
            seacom_ref=task.seacom_ref,
            data={
                "auto_generated": True,
                "auto_generated_source": source,
                "task_description": task.description,
                "site_name": site_name,
                "task_type": str(task.task_type),
                "report_type_resolved": str(resolved_report_type),
                "task_status_at_generation": str(task.status),
                "task_completed_at": task.completed_at.isoformat() if task.completed_at else None,
            },
        )

        try:
            session.add(report)
            session.commit()
            session.refresh(report)
            return report, True
        except IntegrityError:
            # Handles uniqueness races if another process created the report first.
            session.rollback()
            existing_after_race = self._get_active_report_for_task(task.id, session)
            if existing_after_race:
                return existing_after_race, False
            raise

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
            
            # Create notification for technician
            from app.services.notification import _NotificationService, NotificationTemplates
            notification_service = _NotificationService()
            notification_service.create_notification_from_template(
                user_id=technician.user_id,
                template=NotificationTemplates.task_assigned(site.name, data.description),
                session=session,
            )
            
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
        technician_id: UUID | None = None,
        task_type: TaskType | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[TaskResponse]:
        statement = (
            select(Task)
            .options(
                selectinload(Task.site),
                selectinload(Task.technician).selectinload(Technician.user),
            )
            .where(Task.deleted_at.is_(None))
        )  # type: ignore

        if technician_id is not None:
            statement = statement.where(Task.technician_id == technician_id)
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
        """Start a task, ensure auto-report exists, and notify NOC operators."""
        task = self._get_task(task_id, session)
        task.start()
        try:
            session.commit()
            session.refresh(task)

            report, report_created = self._ensure_auto_report_for_task(
                task=task,
                session=session,
                source="task_start",
            )
            
            # Notify NOC operators that task has started
            from app.services.notification import _NotificationService, NotificationTemplates
            notification_service = _NotificationService()
            
            noc_users = session.exec(
                select(User).where(
                    and_(
                        User.role == UserRole.NOC,
                        User.deleted_at.is_(None)
                    )
                )
            ).all()
            
            site_name = task.site.name if task.site else "Unknown Site"
            tech_name = f"{task.technician.user.name} {task.technician.user.surname}" if task.technician else "Unknown"
            
            notification_service.create_notifications_from_template(
                user_ids=(noc_user.id for noc_user in noc_users),
                template=NotificationTemplates.task_started(tech_name, site_name),
                session=session,
            )

            if report_created and task.technician and task.technician.user_id:
                notification_service.create_notification_from_template(
                    user_id=task.technician.user_id,
                    template=NotificationTemplates.report_auto_created(report.report_type, site_name),
                    session=session,
                )
            
            return self.task_to_response(task)
        except IntegrityError as e:
            session.rollback()
            LOG.error("Task start failed. task_id={} reason={}", task_id, e.orig)
            raise ConflictException(f"Error starting task: {e.orig}")
        except Exception as e:
            session.rollback()
            LOG.exception("Unexpected error starting task. task_id={} error={}", task_id, e)
            raise InternalServerErrorException(f"Unexpected error starting task: {e}")
    
    def complete_task(self, task_id: UUID, session: Session) -> TaskResponse:
        """Complete a task, self-heal missing report if needed, and notify NOC operators."""
        task = self._get_task(task_id, session)
        task.complete()
        try:
            session.commit()
            session.refresh(task)

            report, report_created = self._ensure_auto_report_for_task(
                task=task,
                session=session,
                source="task_complete_self_heal",
            )
            
            # Notify NOC operators that task is completed
            from app.services.notification import _NotificationService, NotificationTemplates
            notification_service = _NotificationService()
            
            noc_users = session.exec(
                select(User).where(
                    and_(
                        User.role == UserRole.NOC,
                        User.deleted_at.is_(None)
                    )
                )
            ).all()
            
            site_name = task.site.name if task.site else "Unknown Site"
            tech_name = f"{task.technician.user.name} {task.technician.user.surname}" if task.technician else "Unknown"
            
            notification_service.create_notifications_from_template(
                user_ids=(noc_user.id for noc_user in noc_users),
                template=NotificationTemplates.task_completed(tech_name, site_name),
                session=session,
            )
            
            # Self-heal path notification: report was missing and auto-created at completion.
            if report_created and task.technician and task.technician.user_id:
                notification_service.create_notification_from_template(
                    user_id=task.technician.user_id,
                    template=NotificationTemplates.report_auto_created(report.report_type, site_name),
                    session=session,
                )
            
            return self.task_to_response(task)
        except IntegrityError as e:
            session.rollback()
            LOG.error("Task completion failed. task_id={} reason={}", task_id, e.orig)
            raise ConflictException(f"Error completing task: {e.orig}")
        except Exception as e:
            session.rollback()
            LOG.exception("Unexpected error completing task. task_id={} error={}", task_id, e)
            raise InternalServerErrorException(f"Unexpected error completing task: {e}")
    
    def fail_task(self, task_id: UUID, session: Session) -> TaskResponse:
        """Mark a task as failed and notify NOC operators."""
        task = self._get_task(task_id, session)
        task.fail()
        try:
            session.commit()
            session.refresh(task)
            
            # Notify NOC operators that task has failed
            from app.services.notification import _NotificationService, NotificationTemplates
            notification_service = _NotificationService()
            
            noc_users = session.exec(
                select(User).where(
                    and_(
                        User.role == UserRole.NOC,
                        User.deleted_at.is_(None)
                    )
                )
            ).all()
            
            site_name = task.site.name if task.site else "Unknown Site"
            tech_name = f"{task.technician.user.name} {task.technician.user.surname}" if task.technician else "Unknown"
            
            notification_service.create_notifications_from_template(
                user_ids=(noc_user.id for noc_user in noc_users),
                template=NotificationTemplates.task_failed(tech_name, site_name),
                session=session,
            )
            
            return self.task_to_response(task)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error failing task: {e}")

    def _get_task(self, task_id: UUID, session: Session) -> Task:
        statement = (
            select(Task)
            .options(
                selectinload(Task.site),
                selectinload(Task.technician).selectinload(Technician.user),
            )
            .where(Task.id == task_id, Task.deleted_at.is_(None))
        )  # type: ignore
        task: Task | None = session.exec(statement).first()
        if not task:
            raise NotFoundException("task not found")
        return task


def get_task_service() -> _TaskService:
    return _TaskService()


TaskService = Annotated[_TaskService, Depends(get_task_service)]
