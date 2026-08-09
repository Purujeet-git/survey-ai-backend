"""
Pytest configuration for SurveyAI.

Configures the Windows event loop required by
Psycopg asynchronous database connections.
"""

import asyncio


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