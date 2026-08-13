"""
SurveyAI Backend

Module:
Report API Router

Purpose:
REST API endpoints for generating survey reports and exporting Excel spreadsheets and Word documents.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.reports.schemas.report import ReportGenerateRequest, SurveyReportResponse
from app.reports.services.report_service import ReportService
from app.users.models import User

router = APIRouter(
    prefix="/claims",
    tags=["Reports"],
)


def get_report_service(session: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(session)


@router.post(
    "/{claim_id}/reports/generate",
    response_model=SurveyReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Survey Report, Excel Assessment Sheet, and Word Document",
)
async def generate_survey_report(
    claim_id: UUID,
    payload: ReportGenerateRequest = ReportGenerateRequest(),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_report(
        claim_id=claim_id,
        user_id=current_user.id,
        less_excess=payload.less_excess,
        salvage_value=payload.salvage_value,
        comments=payload.comments,
    )
    return SurveyReportResponse.model_validate(report)


@router.get(
    "/{claim_id}/reports/latest",
    response_model=SurveyReportResponse,
    summary="Get latest generated Survey Report summary",
)
async def get_latest_survey_report(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_latest_claim_report(claim_id)
    return SurveyReportResponse.model_validate(report)


@router.get(
    "/{claim_id}/reports/export/excel",
    summary="Download Surveyor Assessment Excel Spreadsheet (.xlsx) with Preserved Formulas",
)
async def export_report_excel(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_latest_claim_report(claim_id)
    content, media_type, file_name = await service.get_report_bytes(report.id, fmt="excel")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@router.get(
    "/{claim_id}/reports/export/docx",
    summary="Download Official Motor Survey Report Word Document (.docx)",
)
async def export_report_docx(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_latest_claim_report(claim_id)
    content, media_type, file_name = await service.get_report_bytes(report.id, fmt="docx")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
