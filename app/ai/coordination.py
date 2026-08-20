"""Claim-scoped in-process coordination for asynchronous AI work."""

import asyncio
from collections import defaultdict


_claim_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def claim_lock(claim_id: str) -> asyncio.Lock:
    """Return the shared lock for one claim without serializing other claims."""
    if not claim_id:
        raise ValueError("claim_id is required for claim-scoped coordination")
    return _claim_locks[claim_id]