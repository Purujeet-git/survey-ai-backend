"""
SurveyAI Backend

Module:
Conflict Detection Node

Purpose:
Discrepancy generator agent scanning ClaimState to produce itemized Findings (unsupported repairs, date mismatches, anomalies).
"""

from datetime import datetime, timezone
import time
from uuid import uuid4
from app.ai.state import ClaimState, ExecutionLogItem, FindingItem


async def conflict_detection_node(state: ClaimState) -> dict:
    """
    Conflict Detection Node: Scans claim state for contradictions and generates findings.
    """
    start_time = time.time()
    
    validations = state.get("evidence_validation", [])
    extracted = state.get("extracted_entities", {})
    policy = extracted.get("policy", {})
    fir = extracted.get("fir", {})

    findings: list[FindingItem] = []

    # 1. Scan for UNSUPPORTED estimate line items
    for val in validations:
        if val.get("status") == "UNSUPPORTED":
            findings.append({
                "id": str(uuid4()),
                "title": f"Unsupported Repair Claimed: {val.get('estimate_item')}",
                "finding_type": "UNSUPPORTED_REPAIR",
                "severity": "HIGH",
                "description": val.get("reason", "Repair item is not supported by photo or collision evidence."),
                "recommendation": f"Reject claimed cost of INR {val.get('claimed_cost', 0.0):,.2f} for '{val.get('estimate_item')}'.",
            })

    # 2. Check for Policy vs Incident Date consistency
    fir_date = fir.get("incident_date")
    policy_expiry = "2026-12-31"  # Simulated coverage check
    if fir_date and fir_date > policy_expiry:
        findings.append({
            "id": str(uuid4()),
            "title": "Incident Date Outside Policy Coverage",
            "finding_type": "DATE_MISMATCH",
            "severity": "CRITICAL",
            "description": f"Incident date '{fir_date}' occurs after policy expiration '{policy_expiry}'.",
            "recommendation": "Verify policy renewal certificate prior to approving claim payout.",
        })

    # 3. Check for Total Estimate Cost Overrun vs Sum Insured
    sum_insured = policy.get("sum_insured", 750000.0)
    total_estimate = extracted.get("estimate", {}).get("total_amount", 0.0)
    if total_estimate > sum_insured:
        findings.append({
            "id": str(uuid4()),
            "title": "Estimate Amount Exceeds Sum Insured",
            "finding_type": "COST_OVERRUN",
            "severity": "HIGH",
            "description": f"Total repair estimate of INR {total_estimate:,.2f} exceeds policy sum insured of INR {sum_insured:,.2f}.",
            "recommendation": "Process as Constructive Total Loss (CTL) claim.",
        })

    latency = round((time.time() - start_time) * 1000, 2)

    log_entry: ExecutionLogItem = {
        "node": "ConflictDetectionNode",
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency,
        "token_usage": {"input": 600, "output": 250},
        "details": f"Generated {len(findings)} finding(s) / conflict flag(s).",
    }

    return {
        "findings": findings,
        "status": "completed",
        "current_node": "ConflictDetectionNode",
        "execution_logs": [log_entry],
    }
