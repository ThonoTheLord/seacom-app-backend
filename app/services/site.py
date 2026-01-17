from uuid import UUID
from fastapi import Depends
from typing import List, Annotated, Tuple
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.utils.enums import Region
from app.models import Site, SiteCreate, SiteUpdate, SiteResponse
from app.exceptions.http import (
    ConflictException,
    InternalServerErrorException,
    NotFoundException,
)


class _SiteService:
    def site_to_response(self, site: Site) -> SiteResponse:
        coords = site.get_coordinates()
        return SiteResponse(
            id=site.id,
            created_at=site.created_at,
            updated_at=site.updated_at,
            deleted_at=site.deleted_at,
            name=site.name,
            region=site.region,
            address=site.address,
            latitude=coords[0] if coords else None,
            longitude=coords[1] if coords else None,
            geofence_radius=site.geofence_radius,
            num_tasks=len(site.tasks) if site.tasks else 0,
            num_incidents=len(site.incidents) if site.incidents else 0,
            num_reports=0,  # TODO: Add reports relationship if needed
        )

    def create_site(self, data: SiteCreate, session: Session) -> SiteResponse:
        # Extract lat/lon before creating site
        site_data = data.model_dump(exclude={"latitude", "longitude"})
        site: Site = Site(**site_data)
        
        # Set location if coordinates provided
        if data.latitude is not None and data.longitude is not None:
            site.set_location(data.latitude, data.longitude)
        
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

        # Handle location update separately
        lat = update_data.pop("latitude", None)
        lon = update_data.pop("longitude", None)
        
        if lat is not None and lon is not None:
            site.set_location(lat, lon)

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

    def find_nearby_sites(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: float,
        session: Session,
        limit: int = 10
    ) -> List[SiteResponse]:
        """Find sites within a given radius of a point."""
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        
        statement = (
            select(Site)
            .where(Site.deleted_at.is_(None))
            .where(Site.location.isnot(None))
            .where(ST_DWithin(Site.location, point, radius_meters, use_spheroid=True))
            .order_by(ST_Distance(Site.location, point))
            .limit(limit)
        )
        
        sites = session.exec(statement).all()
        return [self.site_to_response(site) for site in sites]

    def is_within_geofence(
        self,
        site_id: UUID,
        latitude: float,
        longitude: float,
        session: Session
    ) -> bool:
        """Check if a point is within the site's geofence."""
        site = self._get_site(site_id, session)
        
        if site.location is None:
            return False
        
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        
        result = session.execute(
            select(ST_DWithin(site.location, point, site.geofence_radius, use_spheroid=True))
        ).scalar()
        
        return bool(result)


def get_site_service() -> _SiteService:
    return _SiteService()


SiteService = Annotated[_SiteService, Depends(get_site_service)]
