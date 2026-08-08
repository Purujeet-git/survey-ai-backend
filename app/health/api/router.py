"""
SurveyAI Backend

Module:
Health API

Purpose:
Provides health and status endpoints for the application.
"""

from fastapi import APIRouter
from app.shared.exceptions import NotFoundError


router = APIRouter(tags=["Health"])


@router.get("/", summary="Application Information")
async def root():
    return {
        "application": "SurveyAI",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/health", summary="Health Check")
async def health():
    return {
        "status": "healthy",
        "service": "SurveyAI Backend",
    }
    


@router.get("/test-error", include_in_schema=False)
async def test_error():
    raise NotFoundError("This is a test exception.")