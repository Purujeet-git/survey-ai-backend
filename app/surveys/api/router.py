"""
SurveyAI Backend

Module:
Survey API Router

Purpose:
Provides authenticated API endpoints for survey and
survey evidence management.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db

from app.surveys.schemas.survey import (
    SurveyCreate,
    SurveyResponse,
    SurveyUpdate,
)

from app.surveys.schemas.evidence import (
    SurveyEvidenceCreate,
    SurveyEvidenceResponse,
    SurveyEvidenceUpdate,
)

from app.surveys.services.survey import SurveyService
from app.surveys.services.evidence import SurveyEvidenceService
from app.surveys.services.evidence_upload import (
    EvidenceUploadService,
)
from app.surveys.storage.local import LocalEvidenceStorage

from app.users.models.user import User


router = APIRouter(
    prefix="/surveys",
    tags=["Surveys"],
)


# ============================================================
# Survey endpoints
# ============================================================


@router.post(
    "",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create survey",
)
async def create_survey(
    data: SurveyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyResponse:
    """
    Create a new survey for a claim owned by
    the authenticated surveyor.
    """

    service = SurveyService(session)

    claim_id = data.claim_id

    survey_data = data.model_dump(
        exclude={"claim_id"},
    )

    survey = await service.create_survey(
        current_user.id,
        claim_id,
        **survey_data,
    )

    await session.commit()

    return SurveyResponse.model_validate(
        survey
    )


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get survey",
)
async def get_survey(
    survey_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyResponse:
    """
    Retrieve a survey belonging to the authenticated
    surveyor.
    """

    service = SurveyService(session)

    survey = await service.get_survey(
        current_user.id,
        survey_id,
    )

    return SurveyResponse.model_validate(
        survey
    )


@router.get(
    "/claim/{claim_id}",
    response_model=list[SurveyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get claim surveys",
)
async def get_claim_surveys(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[SurveyResponse]:
    """
    Retrieve all surveys belonging to a claim owned by
    the authenticated surveyor.
    """

    service = SurveyService(session)

    surveys = await service.get_claim_surveys(
        current_user.id,
        claim_id,
    )

    return [
        SurveyResponse.model_validate(survey)
        for survey in surveys
    ]


@router.patch(
    "/{survey_id}",
    response_model=SurveyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update survey",
)
async def update_survey(
    survey_id: UUID,
    data: SurveyUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyResponse:
    """
    Update a survey belonging to the authenticated
    surveyor.
    """

    service = SurveyService(session)

    survey = await service.update_survey(
        current_user.id,
        survey_id,
        **data.model_dump(
            exclude_unset=True,
        ),
    )

    await session.commit()

    return SurveyResponse.model_validate(
        survey
    )


@router.delete(
    "/{survey_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete survey",
)
async def delete_survey(
    survey_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a survey belonging to the authenticated
    surveyor.
    """

    service = SurveyService(session)

    await service.delete_survey(
        current_user.id,
        survey_id,
    )

    await session.commit()


# ============================================================
# Survey Evidence endpoints
# ============================================================


@router.post(
    "/{survey_id}/evidence",
    response_model=SurveyEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create survey evidence",
)
async def create_evidence(
    survey_id: UUID,
    data: SurveyEvidenceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyEvidenceResponse:
    """
    Create evidence for a survey owned by the
    authenticated surveyor.
    """

    service = SurveyEvidenceService(session)

    evidence_data = data.model_dump(
        exclude={"survey_id"},
    )

    evidence = await service.create_evidence(
        current_user.id,
        survey_id,
        **evidence_data,
    )

    await session.commit()

    return SurveyEvidenceResponse.model_validate(
        evidence
    )


@router.post(
    "/{survey_id}/evidence/upload",
    response_model=SurveyEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload survey evidence",
)
async def upload_evidence(
    survey_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyEvidenceResponse:
    """
    Upload an evidence image for a survey owned by
    the authenticated surveyor.
    """

    evidence_service = SurveyEvidenceService(
        session
    )

    storage = LocalEvidenceStorage()

    upload_service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    try:
        evidence = await upload_service.upload(
            user_id=current_user.id,
            survey_id=survey_id,
            file=file,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await session.commit()

    return SurveyEvidenceResponse.model_validate(
        evidence
    )


@router.get(
    "/{survey_id}/evidence",
    response_model=list[SurveyEvidenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get survey evidence",
)
async def get_survey_evidence(
    survey_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[SurveyEvidenceResponse]:
    """
    Retrieve all evidence belonging to a survey owned
    by the authenticated surveyor.
    """

    service = SurveyEvidenceService(session)

    evidence_list = await service.get_survey_evidence(
        current_user.id,
        survey_id,
    )

    return [
        SurveyEvidenceResponse.model_validate(
            evidence
        )
        for evidence in evidence_list
    ]


@router.get(
    "/evidence/{evidence_id}",
    response_model=SurveyEvidenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get survey evidence item",
)
async def get_evidence(
    evidence_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyEvidenceResponse:
    """
    Retrieve a specific evidence item belonging to
    the authenticated surveyor.
    """

    service = SurveyEvidenceService(session)

    evidence = await service.get_evidence(
        current_user.id,
        evidence_id,
    )

    return SurveyEvidenceResponse.model_validate(
        evidence
    )


@router.patch(
    "/evidence/{evidence_id}",
    response_model=SurveyEvidenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update survey evidence",
)
async def update_evidence(
    evidence_id: UUID,
    data: SurveyEvidenceUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SurveyEvidenceResponse:
    """
    Update evidence belonging to the authenticated
    surveyor.
    """

    service = SurveyEvidenceService(session)

    evidence = await service.update_evidence(
        current_user.id,
        evidence_id,
        **data.model_dump(
            exclude_unset=True,
        ),
    )

    await session.commit()

    return SurveyEvidenceResponse.model_validate(
        evidence
    )


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete survey evidence",
)
async def delete_evidence(
    evidence_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete evidence belonging to the authenticated
    surveyor.
    """

    service = SurveyEvidenceService(session)

    await service.delete_evidence(
        current_user.id,
        evidence_id,
    )

    await session.commit()