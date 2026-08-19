"""
SurveyAI Backend

Module:
LangGraph Shared State Design

Purpose:
Defines the ClaimState typed structure shared across all AI agents in the LangGraph processing pipeline.
"""

from typing import Any, TypedDict, Annotated
import operator


class DocumentItem(TypedDict, total=False):
    id: str
    file_name: str
    document_type: str
    content_type: str
    storage_key: str
    file_size: int
    extracted_text: str
    doc_metadata: dict[str, Any]


class ExtractedEntities(TypedDict, total=False):
    driver: dict[str, Any]
    vehicle: dict[str, Any]
    fir: dict[str, Any]
    policy: dict[str, Any]
    estimate: dict[str, Any]


class AccidentAnalysis(TypedDict, total=False):
    collision_type: str
    impact_direction: str
    estimated_severity: str
    speed_estimate: str
    cause_summary: str
    consistency_analysis: str


class DamagedPart(TypedDict, total=False):
    part_name: str
    severity: str  # Minor, Moderate, Severe, Intact
    recommended_action: str  # REPAIR, REPLACE, PAINT, NO_ACTION
    confidence: float
    bbox: list[float] | None


class PhotoAnalysisResult(TypedDict, total=False):
    detected_parts: list[DamagedPart]
    overall_damage_severity: str
    photo_count: int


class ExpectedDamageResult(TypedDict, total=False):
    expected_zones: list[str]
    expected_components: list[dict[str, Any]]
    confidence: float


class ValidationItem(TypedDict, total=False):
    estimate_item: str
    claimed_cost: float
    status: str  # SUPPORTED, UNSUPPORTED, MANUAL_REVIEW
    confidence: float
    reason: str


class FindingItem(TypedDict, total=False):
    id: str
    title: str
    finding_type: str  # UNSUPPORTED_REPAIR, DATE_MISMATCH, COST_OVERRUN, MISSING_EVIDENCE
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    recommendation: str


class ExecutionLogItem(TypedDict, total=False):
    node: str
    status: str
    timestamp: str
    latency_ms: float
    token_usage: dict[str, int]
    cost_usd: float
    details: str


def compute_token_cost(input_tokens: int, output_tokens: int, model: str = "gemini-1.5-flash") -> float:
    """
    Computes estimated dollar spend based on model input/output rates.
    Fulfills Behavior #10: 'It knows what it cost stage by stage'.
    """
    # Gemini 1.5 Flash rates: $0.075 per 1M input tokens, $0.30 per 1M output tokens
    cost = (input_tokens * 0.000000075) + (output_tokens * 0.00000030)
    return round(cost, 6)



class ClaimState(TypedDict, total=False):
    """
    Central shared state object for LangGraph workflow execution.
    """

    claim_id: str
    claim_number: str
    organization_id: str | None
    user_id: str
    assigned_to_id: str | None
    status: str
    
    # Input manifests
    documents: list[DocumentItem]
    
    # Processed states
    classification_results: dict[str, Any]
    extracted_entities: ExtractedEntities
    accident_analysis: AccidentAnalysis
    photo_analysis: PhotoAnalysisResult
    expected_damage: ExpectedDamageResult
    evidence_validation: list[ValidationItem]
    findings: list[FindingItem]
    decision_events: Annotated[list[dict[str, Any]], operator.add]
    
    # Audit & Monitoring
    execution_logs: Annotated[list[ExecutionLogItem], operator.add]
    current_node: str
    error: str | None
