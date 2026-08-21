"""
SurveyAI Backend

Main application entry point.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.config import settings
from app.config.logging import configure_logging
from app.shared.exceptions import SurveyAIException
from app.shared.exceptions.handlers import survey_ai_exception_handler
from app.shared.middleware.request_id import RequestIDMiddleware
from app.documents.services.watcher_service import WatcherManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting SurveyAI Backend...")
    app.state.watcher_manager = WatcherManager()

    yield

    await app.state.watcher_manager.stop_all()
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

# The frontend URL is configurable for local, preview, and production
# deployments. The JSON login request triggers a browser CORS preflight.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)

    
app.add_exception_handler(
    SurveyAIException,
    survey_ai_exception_handler,
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
