"""
SurveyAI Backend

Module:
Health API

Purpose:
Provides health and status endpoints for the application.
"""

from fastapi import APIRouter

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



