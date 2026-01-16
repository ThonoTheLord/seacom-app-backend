from uuid import UUID
from io import BytesIO
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from sqlalchemy.orm import object_session

from app.utils.enums import ReportType, ReportStatus, NotificationPriority
from app.models import Report, ReportCreate, ReportUpdate, ReportResponse, Task, Technician
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
    ForbiddenException
)
from app.services.pdf import get_pdf_service


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
        """
        Update a report with the provided data.
        Only allows updating: data, attachments, status
        
        Note: The broken audit_report_changes trigger must be dropped in Supabase
        before this will work. Run the fix_trigger.sql script.
        """
        try:
            # Step 1: Fetch the report
            report = self._get_report(report_id, session)
            update_data = data.model_dump(
                exclude_none=True, exclude_defaults=True, exclude_unset=True
            )
            
            print(f"DEBUG: Update data received: {update_data}")

            # Step 2: Validate state
            if report.status in [ReportStatus.COMPLETED]:
                raise ForbiddenException("Cannot update a completed report.")

            # Step 3: Early exit if no data
            if not update_data:
                print(f"DEBUG: No update data, returning current report")
                return self.report_to_response(report)

            # Step 4: Filter allowed fields only
            allowed_fields = {'data', 'attachments', 'status'}
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            if not filtered_data:
                print(f"DEBUG: No allowed fields to update")
                return self.report_to_response(report)

            # Step 5: Apply updates and touch timestamp
            for key, value in filtered_data.items():
                print(f"DEBUG: Setting report.{key}")
                setattr(report, key, value)
            
            report.touch()
            
            # Step 6: Commit changes
            session.add(report)
            session.flush()
            session.commit()
            
            # Step 7: Refresh and return
            session.refresh(report)
            print(f"DEBUG: Report {report_id} updated successfully")
            return self.report_to_response(report)
            
        except ForbiddenException:
            raise
        except NotFoundException:
            raise
        except IntegrityError as e:
            session.rollback()
            print(f"ERROR: Integrity error updating report {report_id}: {e.orig}")
            raise ConflictException(f"Failed to update report: {e.orig}")
        except Exception as e:
            session.rollback()
            error_str = str(e)
            
            # Check if this is the broken trigger error
            if "audit_report_changes" in error_str or "ProgrammingError" in type(e).__name__:
                print(f"ERROR: Trigger error detected. Please drop the broken trigger in Supabase:")
                print(f"  DROP TRIGGER IF EXISTS trg_audit_report_changes ON reports;")
                print(f"  DROP FUNCTION IF EXISTS audit_report_changes() CASCADE;")
            
            print(f"ERROR: Failed to update report {report_id}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise InternalServerErrorException(f"Failed to update report: {str(e)}")

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

    def export_report_pdf(self, report_id: UUID, session: Session) -> tuple[BytesIO, str]:
        """
        Export a completed report as a PDF document.
        
        Args:
            report_id: The UUID of the report to export
            session: Database session
            
        Returns:
            Tuple of (PDF buffer, filename)
            
        Raises:
            NotFoundException: If report not found
            ForbiddenException: If report is not completed
        """
        report = self._get_report(report_id, session)
        
        if report.status != ReportStatus.COMPLETED:
            raise ForbiddenException("Only completed reports can be exported as PDF")
        
        try:
            # Ensure relationships are loaded
            session.refresh(report)
            
            pdf_service = get_pdf_service()
            pdf_buffer = pdf_service.generate_report_pdf(report)
            
            # Verify buffer has content
            pdf_bytes = pdf_buffer.getvalue()
            if not pdf_bytes:
                raise InternalServerErrorException("Failed to generate PDF: empty buffer")
            
            # Generate filename
            report_type = report.report_type.value.replace("-", "_")
            created_date = report.created_at.strftime("%Y%m%d") if report.created_at else "unknown"
            filename = f"report_{report_type}_{created_date}_{str(report.id)[:8]}.pdf"
            
            # Reset buffer for reading
            pdf_buffer.seek(0)
            return pdf_buffer, filename
        except ForbiddenException:
            raise
        except NotFoundException:
            raise
        except Exception as e:
            raise InternalServerErrorException(f"Failed to generate PDF: {str(e)}")



    def _get_report(self, report_id: UUID, session: Session) -> Report:
        statement = select(Report).where(Report.id == report_id, Report.deleted_at.is_(None))  # type: ignore
        report: Report | None = session.exec(statement).first()
        if not report:
            raise NotFoundException("report not found")
        return report


def get_report_service() -> _ReportService:
    return _ReportService()


ReportService = Annotated[_ReportService, Depends(get_report_service)]
