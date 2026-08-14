"""
Central API Router.

All feature routers are registered here.
"""

from fastapi import APIRouter

from app.ai.api.router import router as ai_router
from app.auth.router import router as auth_router
from app.claims.api.router import router as claims_router
from app.documents.api.router import router as documents_router
from app.health.api.router import router as health_router
from app.organizations.api.router import router as organizations_router
from app.reports.api.router import router as reports_router
from app.review.api.router import router as review_router
from app.surveys.api.router import router as surveys_router
from app.timeline.api.router import router as timeline_router
from app.users.api.router import router as users_router

api_router = APIRouter(
    prefix="/api/v1"
)


api_router.include_router(health_router)
api_router.include_router(organizations_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(claims_router)
api_router.include_router(ai_router)
api_router.include_router(review_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)
api_router.include_router(timeline_router)
api_router.include_router(surveys_router)


