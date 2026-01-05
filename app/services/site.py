from uuid import UUID
from fastapi import Depends
from typing import List, Annotated
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.utils.enums import Region
from app.models import Site, SiteCreate, SiteUpdate, SiteResponse
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _SiteService:
    def site_to_response(self, site: Site) -> SiteResponse:
        return SiteResponse(
            **site.model_dump(),
            )

    def create_site(self, data: SiteCreate, session: Session) -> SiteResponse:
        site: Site = Site(**data.model_dump())
        try:
            session.add(site)
            session.commit()
            session.refresh(site)
            return self.site_to_response(site)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error creating site: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error creating site: {e}")

    def read_site(self, site_id: UUID, session: Session) -> SiteResponse:
        site = self._get_site(site_id, session)
        return self.site_to_response(site)

    def read_sites(
        self,
        session: Session,
        region: Region | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[SiteResponse]:
        statement = select(Site).where(Site.deleted_at.is_(None))  # type: ignore

        if region is not None:
            statement = statement.where(Site.region == region)

        statement = statement.offset(offset).limit(limit)
        sites = session.exec(statement).all()
        return [self.site_to_response(site) for site in sites]

    def update_site(
        self, site_id: UUID, data: SiteUpdate, session: Session
    ) -> SiteResponse:
        site = self._get_site(site_id, session)
        update_data = data.model_dump(
            exclude_none=True, exclude_defaults=True, exclude_unset=True
        )

        if not update_data:
            return self.site_to_response(site)

        for k, v in update_data.items():
            setattr(site, k, v)

        site.touch()

        try:
            session.commit()
            session.refresh(site)
            return self.site_to_response(site)
        except IntegrityError as e:
            session.rollback()
            raise ConflictException(f"Error updating site: {e.orig}")
        except Exception as e:
            session.rollback()
            raise InternalServerErrorException(f"Unexpected error updating site: {e}")

    def delete_site(self, site_id: UUID, session: Session) -> None:
        site = self._get_site(site_id, session)
        site.soft_delete()
        session.commit()

    def _get_site(self, site_id: UUID, session: Session) -> Site:
        statement = select(Site).where(Site.id == site_id, Site.deleted_at.is_(None))  # type: ignore
        site: Site | None = session.exec(statement).first()
        if not site:
            raise NotFoundException("site not found")
        return site


def get_site_service() -> _SiteService:
    return _SiteService()


SiteService = Annotated[_SiteService, Depends(get_site_service)]
