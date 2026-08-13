"""
SurveyAI Backend

Module:
Organization API Router

Purpose:
REST API endpoints for Organization management.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.database.enums import UserRole
from app.organizations.repositories.organization_repository import OrganizationRepository
from app.organizations.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.organizations.services.organization_service import OrganizationService
from app.users.models import User

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


def get_organization_service(
    session: AsyncSession = Depends(get_db),
) -> OrganizationService:
    repository = OrganizationRepository(session)
    return OrganizationService(repository)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Organization",
)
async def create_organization(
    schema: OrganizationCreate,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    return await service.create_organization(schema)


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List all Organizations",
)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_organizations(skip=skip, limit=limit)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get Organization by ID",
)
async def get_organization(
    organization_id: UUID,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_organization(organization_id)


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update an Organization",
)
async def update_organization(
    organization_id: UUID,
    schema: OrganizationUpdate,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.ADMIN)),
):
    return await service.update_organization(organization_id, schema)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an Organization",
)
async def delete_organization(
    organization_id: UUID,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    await service.delete_organization(organization_id)
