from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from app.utils.enums import ReportType, ReportStatus, NotificationPriority
from app.models import Report, ReportCreate, ReportUpdate, ReportResponse, Task, Technician
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
    ForbiddenException
)


class _ReportService:
    def report_to_response(self, report: Report) -> ReportResponse:
        user = report.technician.user
        return ReportResponse(
            **report.model_dump(),
            technician_fullname=f"{user.name} {user.surname}"
            )

    def create_report(self, data: ReportCreate, session: Session) -> ReportResponse:
        report: Report = Report(**data.model_dump())
        try:
            session.add(report)
            session.commit()
            session.refresh(report)
            
            # Get task and technician info for notification
            task = session.exec(select(Task).where(Task.id == data.task_id)).first()
            technician = session.exec(select(Technician).where(Technician.id == data.technician_id)).first()
            
            if task and technician:
                # Create notification for NOC operators about new report
                from app.services.notification import _NotificationService
                from app.models import User
                from app.utils.enums import UserRole
                
                notification_service = _NotificationService()
                
                # Notify all NOC operators
                noc_users = session.exec(
                    select(User).where(
                        and_(
                            User.role == UserRole.NOC,
                            User.deleted_at.is_(None)
                        )
                    )
                ).all()
                
                # Get site name safely
                site_name = task.site.name if task.site else "Unknown Site"
                technician_name = technician.user.name if technician.user else "Unknown Technician"
                
                for noc_user in noc_users:
                    notification_service.create_notification_for_user(
                        user_id=noc_user.id,
                        title=f"New Report Submitted",
                        message=f"{technician_name} submitted a {data.report_type} report for task at {site_name}",
                        priority=NotificationPriority.NORMAL,
                        session=session
                    )
            
            return self.report_to_response(report)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating report: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating report: {e}")

    def read_report(self, report_id: UUID, session: Session) -> ReportResponse:
        report = self._get_report(report_id, session)
        return self.report_to_response(report)

    def read_reports(
        self,
        session: Session,
        report_type: ReportType | None = None,
        status: ReportStatus | None = None,
        technician_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[ReportResponse]:
        statement = select(Report).where(Report.deleted_at.is_(None))  # type: ignore

        if report_type is not None:
            statement = statement.where(Report.report_type == report_type)
        if status is not None:
            statement = statement.where(Report.status == status)
        if technician_id is not None:
            statement = statement.where(Report.technician_id == technician_id)

        statement = statement.offset(offset).limit(limit)
        reports = session.exec(statement).all()
        return [self.report_to_response(report) for report in reports]

    def update_report(
        self, report_id: UUID, data: ReportUpdate, session: Session
    ) -> ReportResponse:
        report = self._get_report(report_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if report.status in [ReportStatus.COMPLETED]:
            raise ForbiddenException("Cannot update a completed report.")

        if not update_data:
            return self.report_to_response(report)

        for k, v in update_data.items():
            setattr(report, k, v)

        report.touch()

        try:
            session.commit()
            session.refresh(report)
            return self.report_to_response(report)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating report: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating report: {e}")

    def delete_report(self, report_id: UUID, session: Session) -> None:
        report = self._get_report(report_id, session)
        report.soft_delete()
        session.commit()
    
    def start_report(self, report_id: UUID, session: Session) -> ReportResponse:
        """"""
        report = self._get_report(report_id, session)
        report.start()
        try:
            session.commit()
            session.refresh(report)
            return self.report_to_response(report)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error starting report: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error starting report: {e}")
    
    def complete_report(self, report_id: UUID, session: Session) -> ReportResponse:
        """"""
        report = self._get_report(report_id, session)
        report.complete()
        try:
            session.commit()
            session.refresh(report)
            return self.report_to_response(report)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error completing report: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error completing report: {e}")

    def _get_report(self, report_id: UUID, session: Session) -> Report:
        statement = select(Report).where(Report.id == report_id, Report.deleted_at.is_(None))  # type: ignore
        report: Report | None = session.exec(statement).first()
        if not report:
            raise NotFoundException("report not found")
        return report


def get_report_service() -> _ReportService:
    return _ReportService()


ReportService = Annotated[_ReportService, Depends(get_report_service)]
