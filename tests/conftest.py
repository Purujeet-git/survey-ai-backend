"""
Pytest configuration for SurveyAI.

Configures the Windows event loop required by
Psycopg asynchronous database connections.
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Use the Selector event loop on Windows.

    Psycopg asynchronous connections are incompatible
    with the Windows ProactorEventLoop.
    """

    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        return asyncio.WindowsSelectorEventLoopPolicy()

    return asyncio.DefaultEventLoopPolicy()