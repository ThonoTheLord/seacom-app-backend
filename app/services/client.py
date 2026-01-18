from uuid import UUID, uuid4
from typing import Annotated, List
from fastapi import Depends

from sqlmodel import Session, select

from app.models import Client, ClientCreate, ClientUpdate, ClientResponse
from app.database import get_session
from app.exceptions.http import NotFoundException, ConflictException


class ClientService:
    """Service for managing clients."""

    def create_client(self, payload: ClientCreate, session: Session) -> ClientResponse:
        """Create a new client."""
        # Check if client with same name exists
        existing = session.exec(
            select(Client).where(Client.name == payload.name)
        ).first()
        if existing:
            raise ConflictException(f"Client with name '{payload.name}' already exists")
        client = Client.model_validate(payload)

        # Ensure DB `code` column is unique and not empty. Generate one if absent.
        # Use a simple slug from the name trimmed to fit column, and append a short uuid suffix on collisions.
        base = ''.join(ch for ch in payload.name.lower() if ch.isalnum())[:16] or 'client'
        candidate = base
        # If candidate is empty string for any reason, use uuid
        if not candidate:
            candidate = uuid4().hex[:16]

        # Check uniqueness and append suffix until unique
        while session.exec(select(Client).where(Client.code == candidate)).first():
            candidate = f"{base[:12]}{uuid4().hex[:4]}"

        client.code = candidate
        session.add(client)
        session.commit()
        session.refresh(client)
        return ClientResponse.model_validate(client)

    def read_clients(
        self,
        session: Session,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 100
    ) -> List[ClientResponse]:
        """Read all clients."""
        query = select(Client)
        if active_only:
            query = query.where(Client.is_active == True)
        query = query.order_by(Client.name).offset(offset).limit(limit)
        
        clients = session.exec(query).all()
        return [ClientResponse.model_validate(c) for c in clients]

    def read_client(self, client_id: UUID, session: Session) -> ClientResponse:
        """Read a single client by ID."""
        client = session.get(Client, client_id)
        if not client:
            raise NotFoundException(f"Client with ID {client_id} not found")
        return ClientResponse.model_validate(client)

    def update_client(
        self,
        client_id: UUID,
        payload: ClientUpdate,
        session: Session
    ) -> ClientResponse:
        """Update a client."""
        client = session.get(Client, client_id)
        if not client:
            raise NotFoundException(f"Client with ID {client_id} not found")
        
        update_data = payload.model_dump(exclude_unset=True)
        
        # Check for conflicts if name is being updated
        if "name" in update_data:
            existing = session.exec(
                select(Client).where(
                    Client.name == update_data["name"],
                    Client.id != client_id
                )
            ).first()
            if existing:
                raise ConflictException(f"Client with name '{update_data['name']}' already exists")
        
        for key, value in update_data.items():
            setattr(client, key, value)
        
        client.touch()
        session.add(client)
        session.commit()
        session.refresh(client)
        return ClientResponse.model_validate(client)

    def delete_client(self, client_id: UUID, session: Session) -> None:
        """Delete a client (soft delete by deactivating)."""
        client = session.get(Client, client_id)
        if not client:
            raise NotFoundException(f"Client with ID {client_id} not found")
        
        # Soft delete - just deactivate
        client.is_active = False
        client.touch()
        session.add(client)
        session.commit()


def get_client_service() -> ClientService:
    return ClientService()


ClientServiceDep = Annotated[ClientService, Depends(get_client_service)]
