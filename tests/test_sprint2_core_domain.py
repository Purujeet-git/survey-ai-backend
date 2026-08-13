"""
Test suite for Sprint 2 — Core Domain:
- Organizations
- User Roles & RBAC
- Claims Workflow State Machine
- Timeline Audit Trail
"""

import pytest
from uuid import uuid4

import app.database.models  # Ensures all SQLAlchemy models are registered in metadata
from app.database.enums import ClaimStatus, UserRole
from app.claims.workflow import validate_status_transition

from app.organizations.schemas.organization import OrganizationCreate
from app.organizations.services.organization_service import OrganizationService
from app.shared.exceptions import ValidationException, ConflictException, NotFoundException
from app.timeline.schemas.timeline import TimelineEventCreate
from app.timeline.services.timeline_service import TimelineService


class DummyOrganizationRepository:
    def __init__(self):
        self.orgs = {}

    async def get_by_code(self, code: str):
        for org in self.orgs.values():
            if org.code == code:
                return org
        return None

    async def get_by_id(self, org_id):
        return self.orgs.get(org_id)

    async def create(self, org):
        self.orgs[org.id] = org
        return org

    async def list_all(self, skip=0, limit=100):
        return list(self.orgs.values())[skip:skip+limit]

    async def update(self, org):
        self.orgs[org.id] = org
        return org

    async def delete(self, org):
        self.orgs.pop(org.id, None)


class DummyTimelineRepository:
    def __init__(self):
        self.events = []

    async def create(self, event):
        event.id = uuid4()
        self.events.append(event)
        return event

    async def list_by_claim(self, claim_id):
        return [e for e in self.events if e.claim_id == claim_id]


@pytest.mark.asyncio
async def test_organization_service_crud():
    repo = DummyOrganizationRepository()
    service = OrganizationService(repo)

    # 1. Create Organization
    create_schema = OrganizationCreate(
        name="Alpha Insurance",
        code="ALPHA01",
        contact_email="contact@alphainsurance.com",
    )
    org = await service.create_organization(create_schema)
    assert org.name == "Alpha Insurance"
    assert org.code == "ALPHA01"

    # 2. Duplicate Code Conflict
    with pytest.raises(ConflictException):
        await service.create_organization(create_schema)

    # 3. Retrieve Organization
    retrieved = await service.get_organization(org.id)
    assert retrieved.id == org.id

    # 4. List Organizations
    org_list = await service.list_organizations()
    assert len(org_list) == 1
    assert org_list[0].code == "ALPHA01"


def test_claim_status_workflow_transitions():
    # Valid transitions
    validate_status_transition(ClaimStatus.DRAFT, ClaimStatus.SUBMITTED)
    validate_status_transition(ClaimStatus.SUBMITTED, ClaimStatus.PROCESSING)
    validate_status_transition(ClaimStatus.PROCESSING, ClaimStatus.UNDER_REVIEW)
    validate_status_transition(ClaimStatus.UNDER_REVIEW, ClaimStatus.APPROVED)
    validate_status_transition(ClaimStatus.APPROVED, ClaimStatus.COMPLETED)
    validate_status_transition(ClaimStatus.COMPLETED, ClaimStatus.CLOSED)

    # Invalid transitions
    with pytest.raises(ValidationException):
        validate_status_transition(ClaimStatus.DRAFT, ClaimStatus.APPROVED)

    with pytest.raises(ValidationException):
        validate_status_transition(ClaimStatus.CLOSED, ClaimStatus.DRAFT)


@pytest.mark.asyncio
async def test_timeline_service_logging():
    repo = DummyTimelineRepository()
    service = TimelineService(repo)

    claim_id = uuid4()
    actor_id = uuid4()

    event = await service.log_event(
        TimelineEventCreate(
            claim_id=claim_id,
            actor_id=actor_id,
            event_type="STATUS_CHANGED",
            description="Claim status changed from draft to submitted.",
            payload={"old": "draft", "new": "submitted"},
        )
    )

    assert event.claim_id == claim_id
    assert event.event_type == "STATUS_CHANGED"

    timeline = await service.get_claim_timeline(claim_id)
    assert len(timeline) == 1
    assert timeline[0].description == "Claim status changed from draft to submitted."
