from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.utils.enums import IncidentStatus, NotificationPriority
from app.models import Incident, IncidentCreate, IncidentUpdate, IncidentResponse, Site, Technician, User
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _IncidentService:
    def incident_to_response(self, incident: Incident) -> IncidentResponse:
        user = incident.technician.user
        return IncidentResponse(
            **incident.model_dump(),
            site_name=incident.site.name,
            technician_fullname=f"{user.name} {user.surname}",
            num_attachments=len(incident.attachments or [])
            )

    def create_incident(self, data: IncidentCreate, session: Session) -> IncidentResponse:
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

        incident: Incident = Incident(**data.model_dump(), site=site, technician=technician)
        try:
            session.add(incident)
            session.commit()
            session.refresh(incident)
            
            # Create notification for NOC operators about new incident
            from app.services.notification import _NotificationService
            from app.utils.enums import UserRole
            
            notification_service = _NotificationService()
            
            # Notify all NOC operators
            noc_users = session.exec(
                select(User).where(
                    User.role == UserRole.NOC,
                    User.deleted_at.is_(None)
                )
            ).all()
            
            for noc_user in noc_users:
                notification_service.create_notification_for_user(
                    user_id=noc_user.id,
                    title=f"New Incident Reported",
                    message=f"Critical incident reported at {site.name} by {technician.user.name}. {data.description[:80]}...",
                    priority=NotificationPriority.CRITICAL,
                    session=session
                )
            
            return self.incident_to_response(incident)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating incident: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating incident: {e}")

    def read_incident(self, incident_id: UUID, session: Session) -> IncidentResponse:
        incident = self._get_incident(incident_id, session)
        return self.incident_to_response(incident)

    def read_incidents(
        self,
        session: Session,
        technician_id: UUID | None = None,
        status: IncidentStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[IncidentResponse]:
        statement = select(Incident).where(Incident.deleted_at.is_(None))  # type: ignore

        if technician_id is not None:
            statement = statement.where(Incident.technician_id == technician_id)
        if status is not None:
            statement = statement.where(Incident.status == status)

        statement = statement.offset(offset).limit(limit)
        incidents = session.exec(statement).all()
        return [self.incident_to_response(incident) for incident in incidents]

    def update_incident(
        self, incident_id: UUID, data: IncidentUpdate, session: Session
    ) -> IncidentResponse:
        incident = self._get_incident(incident_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if not update_data:
            return self.incident_to_response(incident)

        for k, v in update_data.items():
            setattr(incident, k, v)

        incident.touch()

        try:
            session.commit()
            session.refresh(incident)
            return self.incident_to_response(incident)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating incident: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating incident: {e}")

    def delete_incident(self, incident_id: UUID, session: Session) -> None:
        incident = self._get_incident(incident_id, session)
        incident.soft_delete()
        session.commit()
    
    def start_incident(self, incident_id: UUID, session: Session) -> IncidentResponse:
        """"""
        incident = self._get_incident(incident_id, session)
        incident.start()
        try:
            session.commit()
            session.refresh(incident)
            return self.incident_to_response(incident)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error starting incident: {e}")
    
    def resolve_incident(self, incident_id: UUID, session: Session) -> IncidentResponse:
        """"""
        incident = self._get_incident(incident_id, session)
        incident.resolve()
        try:
            session.commit()
            session.refresh(incident)
            return self.incident_to_response(incident)
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error resolving incident: {e}")

    def _get_incident(self, incident_id: UUID, session: Session) -> Incident:
        statement = select(Incident).where(Incident.id == incident_id, Incident.deleted_at.is_(None))  # type: ignore
        incident: Incident | None = session.exec(statement).first()
        if not incident:
            raise NotFoundException("incident not found")
        return incident


def get_incident_service() -> _IncidentService:
    return _IncidentService()


IncidentService = Annotated[_IncidentService, Depends(get_incident_service)]
