"""
SurveyAI Backend

Module:
Organization Service

Purpose:
Encapsulates business logic for managing Organizations.
"""

from uuid import UUID

from app.organizations.models.organization import Organization
from app.organizations.repositories.organization_repository import OrganizationRepository
from app.organizations.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.shared.exceptions import ConflictException, NotFoundException


class OrganizationService:
    """
    Business logic service for Organizations.
    """

    def __init__(self, repository: OrganizationRepository) -> None:
        self.repository = repository

    async def create_organization(self, schema: OrganizationCreate) -> Organization:
        existing = await self.repository.get_by_code(schema.code)
        if existing:
            raise ConflictException(f"Organization code '{schema.code}' already exists.")

        organization = Organization(
            name=schema.name,
            code=schema.code,
            contact_email=schema.contact_email,
            address=schema.address,
            settings=schema.settings,
        )
        return await self.repository.create(organization)

    async def get_organization(self, organization_id: UUID) -> Organization:
        organization = await self.repository.get_by_id(organization_id)
        if not organization:
            raise NotFoundException(f"Organization with ID '{organization_id}' not found.")
        return organization

    async def list_organizations(self, skip: int = 0, limit: int = 100) -> list[Organization]:
        return await self.repository.list_all(skip=skip, limit=limit)

    async def update_organization(
        self, organization_id: UUID, schema: OrganizationUpdate
    ) -> Organization:
        organization = await self.get_organization(organization_id)

        if schema.code is not None and schema.code != organization.code:
            existing = await self.repository.get_by_code(schema.code)
            if existing:
                raise ConflictException(f"Organization code '{schema.code}' already exists.")
            organization.code = schema.code

        if schema.name is not None:
            organization.name = schema.name
        if schema.contact_email is not None:
            organization.contact_email = schema.contact_email
        if schema.address is not None:
            organization.address = schema.address
        if schema.status is not None:
            organization.status = schema.status
        if schema.settings is not None:
            organization.settings = schema.settings

        return await self.repository.update(organization)

    async def delete_organization(self, organization_id: UUID) -> None:
        organization = await self.get_organization(organization_id)
        await self.repository.delete(organization)
