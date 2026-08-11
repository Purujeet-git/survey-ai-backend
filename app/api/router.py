"""
Central API Router.

All feature routers are registered here.
"""

from fastapi import APIRouter

from app.health.api.router import router as health_router
from app.users.api.router import router as users_router

from app.auth.router import router as auth_router
from app.claims.api.router import router as claims_router
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(claims_router)