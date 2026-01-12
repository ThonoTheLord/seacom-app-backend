from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.models import Technician, TechnicianCreate, TechnicianUpdate, TechnicianResponse, User
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _TechnicianService:
    def technician_to_response(self, technician: Technician) -> TechnicianResponse:
        return TechnicianResponse(
            **technician.model_dump(),
            fullname=f"{technician.user.name} {technician.user.surname}"
            )

    def create_technician(self, data: TechnicianCreate, session: Session) -> TechnicianResponse:
        # Handle user
        statement = select(User).where(User.id == data.user_id, User.deleted_at.is_(None)) # type: ignore
        user: User | None = session.exec(statement).first()

        if not user:
            raise NotFoundException("user not found, cannot create technician.")
        
        technician: Technician = Technician(**data.model_dump(), user=user)
        try:
            session.add(technician)
            session.commit()
            session.refresh(technician)
            return self.technician_to_response(technician)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating technician: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating technician: {e}")

    def read_technician(self, technician_id: UUID, session: Session) -> TechnicianResponse:
        technician = self._get_technician(technician_id, session)
        return self.technician_to_response(technician)

    def read_technicians(
        self,
        session: Session,
        offset: int = 0,
        limit: int = 100,
    ) -> List[TechnicianResponse]:
        statement = select(Technician).where(Technician.deleted_at.is_(None))  # type: ignore
        statement = statement.offset(offset).limit(limit)
        technicians = session.exec(statement).all()
        return [self.technician_to_response(technician) for technician in technicians]

    def update_technician(
        self, technician_id: UUID, data: TechnicianUpdate, session: Session
    ) -> TechnicianResponse:
        technician = self._get_technician(technician_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if not update_data:
            return self.technician_to_response(technician)

        for k, v in update_data.items():
            setattr(technician, k, v)

        technician.touch()

        try:
            session.commit()
            session.refresh(technician)
            return self.technician_to_response(technician)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating technician: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating technician: {e}")

    def delete_technician(self, technician_id: UUID, session: Session) -> None:
        technician = self._get_technician(technician_id, session)
        technician.soft_delete()
        session.commit()

    def _get_technician(self, technician_id: UUID, session: Session) -> Technician:
        statement = (
            select(Technician)
            .where(Technician.id == technician_id)
            .where(Technician.deleted_at.is_(None)) # type: ignore
          )  
        technician: Technician | None = session.exec(statement).first()
        if not technician:
            raise NotFoundException("technician not found")
        return technician


def get_technician_service() -> _TechnicianService:
    return _TechnicianService()


TechnicianService = Annotated[_TechnicianService, Depends(get_technician_service)]
