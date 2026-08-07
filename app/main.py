"""
SurveyAI Backend

Main application entry point.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.config import settings
from app.config.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting SurveyAI Backend...")

    yield

    logger.info("Stopping SurveyAI Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": "/api/v1",
    }