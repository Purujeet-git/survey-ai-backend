"""
Pytest configuration for SurveyAI.

Configures the Windows event loop required by
Psycopg asynchronous database connections and
provides reusable database fixtures for tests.
"""

import asyncio

import pytest_asyncio

from app.database import AsyncSessionLocal


def pytest_configure(config):
    """
    Configure the Windows event loop policy for pytest.

    Psycopg asynchronous connections require the Selector
    event loop on Windows.
    """

    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )


@pytest_asyncio.fixture
async def async_session():
    """
    Provide an asynchronous database session for tests.
    """

    async with AsyncSessionLocal() as session:
        yield session

        await session.rollback()