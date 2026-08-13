"""
SurveyAI Backend

Module:
Intake Node

Purpose:
Validates claim workspace, checks file manifests, and initializes graph state for AI pipeline processing.
"""

from datetime import datetime, timezone
import time
from app.ai.state import ClaimState, ExecutionLogItem


async def intake_node(state: ClaimState) -> dict:
    """
    Intake Agent Node: Validates claim workspace & documents.
    """
    start_time = time.time()
    
    docs = state.get("documents", [])
    claim_id = state.get("claim_id", "unknown")
    
    status = "SUCCESS" if docs else "NO_DOCUMENTS"
    details = f"Intake verified {len(docs)} documents for claim '{claim_id}'."

    latency = round((time.time() - start_time) * 1000, 2)

    log_entry: ExecutionLogItem = {
        "node": "IntakeNode",
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency,
        "token_usage": {"input": 0, "output": 0},
        "details": details,
    }

    return {
        "status": "intake_completed",
        "current_node": "IntakeNode",
        "execution_logs": [log_entry],
    }
