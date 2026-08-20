"""
SurveyAI Backend

Module:
LangGraph Pipeline Assembly

Purpose:
Compiles and executes the complete LangGraph StateGraph workflow for claim processing & damage intelligence.
"""

from langgraph.graph import END, START, StateGraph

from app.ai.checkpointer import global_checkpointer
from app.ai.nodes.accident import accident_understanding_node
from app.ai.nodes.classification import classification_node
from app.ai.nodes.conflict_detection import conflict_detection_node
from app.ai.nodes.evidence_validation import evidence_validation_node
from app.ai.nodes.expected_damage import expected_damage_node
from app.ai.nodes.extraction import extraction_node
from app.ai.nodes.intake import intake_node
from app.ai.nodes.photo_analysis import photo_analysis_node
from app.ai.state import ClaimState, compute_token_cost
from app.ai.security_guardrails import SecurityGuardrails
from app.ai.coordination import claim_lock
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import time


def build_claim_processing_graph():
    """
    Constructs the full LangGraph StateGraph workflow.
    """
    workflow = StateGraph(ClaimState)

    nodes = {
        "IntakeNode": intake_node,
        "ClassificationNode": classification_node,
        "ExtractionNode": extraction_node,
        "AccidentUnderstandingNode": accident_understanding_node,
        "PhotoAnalysisNode": photo_analysis_node,
        "ExpectedDamageNode": expected_damage_node,
        "EvidenceValidationNode": evidence_validation_node,
        "ConflictDetectionNode": conflict_detection_node,
    }

    async def escalation_node(state):
        """Stop safely when the agent cannot proceed without a human or more evidence."""
        return {
            "status": "awaiting_human_intervention",
            "current_node": "HumanEscalationNode",
            "error": "No source documents were provided. Upload evidence before processing.",
            "execution_logs": [{
                "node": "HumanEscalationNode",
                "status": "ESCALATED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency_ms": 0.0,
                "token_usage": {"input": 0, "output": 0},
                "cost_usd": 0.0,
                "details": "Paused safely: the agent needs source evidence before it can make a grounded decision.",
            }],
        }

    async def manual_review_preparation_node(state):
        """Make the human-review handoff an explicit, observable stage."""
        start = time.time()
        manual_count = sum(1 for item in state.get("evidence_validation", []) if item.get("status") == "MANUAL_REVIEW")
        return {
            "status": "awaiting_human_review",
            "current_node": "HumanReviewPreparationNode",
            "execution_logs": [{
                "node": "HumanReviewPreparationNode",
                "status": "ESCALATED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency_ms": round((time.time() - start) * 1000, 2),
                "token_usage": {"input": 0, "output": 0},
                "cost_usd": 0.0,
                "details": f"Escalated {manual_count} uncertain evidence item(s) to the human review gate.",
            }],
        }

    def make_checkpointed_node(node_name, node_fn):
        async def checkpointed_node(state):
            result = await node_fn(state)
            result = deepcopy(result)
            for log in result.get("execution_logs", []):
                tokens = log.get("token_usage", {}) or {}
                if "cost_usd" not in log:
                    log["cost_usd"] = compute_token_cost(
                        int(tokens.get("input", 0) or 0),
                        int(tokens.get("output", 0) or 0),
                    )
            merged = deepcopy(dict(state))
            for key, value in result.items():
                if key == "execution_logs":
                    merged[key] = list(state.get(key, [])) + list(value or [])
                else:
                    merged[key] = value
            merged["current_node"] = node_name
            global_checkpointer.save_checkpoint(state.get("claim_id", ""), merged)
            return result
        return checkpointed_node

    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, make_checkpointed_node(node_name, node_fn))
    workflow.add_node("HumanEscalationNode", make_checkpointed_node("HumanEscalationNode", escalation_node))
    workflow.add_node("HumanReviewPreparationNode", make_checkpointed_node("HumanReviewPreparationNode", manual_review_preparation_node))

    def route_after_intake(state):
        return "ClassificationNode" if state.get("documents") else "HumanEscalationNode"

    def route_after_validation(state):
        has_manual_review = any(item.get("status") == "MANUAL_REVIEW" for item in state.get("evidence_validation", []))
        return "HumanReviewPreparationNode" if has_manual_review else "ConflictDetectionNode"

    def route_after_resume(state):
        """Enter immediately after the last durable checkpointed stage."""
        next_nodes = {
            "START": "IntakeNode",
            "": "IntakeNode",
            "IntakeNode": "ClassificationNode",
            "ClassificationNode": "ExtractionNode",
            "ExtractionNode": "AccidentUnderstandingNode",
            "AccidentUnderstandingNode": "PhotoAnalysisNode",
            "PhotoAnalysisNode": "ExpectedDamageNode",
            "ExpectedDamageNode": "EvidenceValidationNode",
            "EvidenceValidationNode": "ConflictDetectionNode",
            "HumanReviewPreparationNode": "ConflictDetectionNode",
            "ConflictDetectionNode": END,
            "HumanEscalationNode": END,
        }
        return next_nodes.get(state.get("current_node", "START"), "IntakeNode")

    workflow.add_conditional_edges(START, route_after_resume)
    workflow.add_conditional_edges("IntakeNode", route_after_intake)
    workflow.add_edge("HumanEscalationNode", END)
    workflow.add_edge("ClassificationNode", "ExtractionNode")
    workflow.add_edge("ExtractionNode", "AccidentUnderstandingNode")
    workflow.add_edge("AccidentUnderstandingNode", "PhotoAnalysisNode")
    workflow.add_edge("PhotoAnalysisNode", "ExpectedDamageNode")
    workflow.add_edge("ExpectedDamageNode", "EvidenceValidationNode")
    workflow.add_conditional_edges("EvidenceValidationNode", route_after_validation)
    workflow.add_edge("HumanReviewPreparationNode", "ConflictDetectionNode")
    workflow.add_edge("ConflictDetectionNode", END)

    return workflow.compile()


class ClaimAIPipelineService:
    """
    Orchestration service for executing and resuming the Claim AI Processing Pipeline.
    """

    def __init__(self) -> None:
        self.graph = build_claim_processing_graph()

    @staticmethod
    def _input_fingerprint(state: ClaimState) -> str:
        """Hash the source manifest so identical runs can be recognized safely."""
        manifest = []
        for document in state.get("documents", []):
            manifest.append({
                "id": document.get("id"),
                "file_name": document.get("file_name"),
                "document_type": document.get("document_type"),
                "content_type": document.get("content_type"),
                "extracted_text": document.get("extracted_text", ""),
            })
        payload = json.dumps(manifest, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _prepare_untrusted_documents(state: ClaimState) -> ClaimState:
        """Create the agent view of documents without mutating stored originals."""
        prepared = deepcopy(dict(state))
        documents = []
        for source in state.get("documents", []):
            document = deepcopy(source)
            raw_text = document.get("extracted_text", "") or ""
            metadata = dict(document.get("doc_metadata", {}) or {})
            if raw_text.startswith("<untrusted_source_document_data>"):
                safe_text = raw_text
                detected = bool(document.get("injection_detected", metadata.get("prompt_injection_detected", False)))
            else:
                safe_text, detected = SecurityGuardrails.sanitize_untrusted_text(raw_text)
            document["extracted_text"] = safe_text
            document["injection_detected"] = detected
            metadata["prompt_injection_detected"] = detected
            document["doc_metadata"] = metadata
            documents.append(document)
        prepared["documents"] = documents
        return prepared

    @staticmethod
    def _decision_for(node_name: str, state: ClaimState) -> dict:
        """Translate agent state into a human-readable routing decision."""
        if node_name == "IntakeNode":
            if state.get("documents"):
                return {"stage": node_name, "decision": "CONTINUE", "label": "Evidence found", "reason": f"{len(state['documents'])} source document(s) are available for analysis.", "next_node": "ClassificationNode", "tone": "positive"}
            return {"stage": node_name, "decision": "ESCALATE", "label": "Human action needed", "reason": "No source documents are available, so the agent will not infer claim facts.", "next_node": "HumanEscalationNode", "tone": "warning"}
        if node_name == "EvidenceValidationNode":
            manual = sum(1 for item in state.get("evidence_validation", []) if item.get("status") == "MANUAL_REVIEW")
            if manual:
                return {"stage": node_name, "decision": "ESCALATE", "label": "Route to review", "reason": f"{manual} evidence item(s) are uncertain and require a person before commitment.", "next_node": "HumanReviewPreparationNode", "tone": "warning"}
            return {"stage": node_name, "decision": "CONTINUE", "label": "Evidence is consistent", "reason": "No uncertain evidence items require an early handoff.", "next_node": "ConflictDetectionNode", "tone": "positive"}
        if node_name == "ConflictDetectionNode":
            findings = len(state.get("findings", []))
            return {"stage": node_name, "decision": "ESCALATE" if findings else "CLEAR", "label": "Human review required" if findings else "No findings", "reason": f"{findings} finding(s) were staged for item-by-item review." if findings else "The available sources produced no findings.", "next_node": "Human Review Gate" if findings else "Complete", "tone": "warning" if findings else "positive"}
        return {"stage": node_name, "decision": "CONTINUE", "label": "Continue analysis", "reason": "The stage completed successfully and its output is available to the next agent.", "next_node": "Next stage", "tone": "neutral"}

    async def run_pipeline(self, initial_state: ClaimState) -> ClaimState:
        """
        Execute or resume the graph pipeline for a claim.
        """
        claim_id = initial_state.get("claim_id", "")
        input_fingerprint = self._input_fingerprint(initial_state)
        async with claim_lock(claim_id):
            existing_checkpoint = global_checkpointer.load_checkpoint(claim_id)
            if (
                existing_checkpoint
                and existing_checkpoint.get("input_fingerprint") == input_fingerprint
                and existing_checkpoint.get("current_node") in {"ConflictDetectionNode", "HumanEscalationNode"}
            ):
                return existing_checkpoint

            source_state = deepcopy(existing_checkpoint or initial_state)
            source_state["input_fingerprint"] = input_fingerprint
            current_state = self._prepare_untrusted_documents(source_state)
            result_state = await self.graph.ainvoke(current_state)
            result_state["input_fingerprint"] = input_fingerprint
            global_checkpointer.save_checkpoint(claim_id, result_state)
            return result_state

    async def astream_pipeline(self, initial_state: ClaimState):
        """
        Stream stage-by-stage node execution events for real-time UI visualization.
        """
        claim_id = initial_state.get("claim_id", "")
        input_fingerprint = self._input_fingerprint(initial_state)
        async with claim_lock(claim_id):
            existing_checkpoint = global_checkpointer.load_checkpoint(claim_id)
            if (
                existing_checkpoint
                and existing_checkpoint.get("input_fingerprint") == input_fingerprint
                and existing_checkpoint.get("current_node") in {"ConflictDetectionNode", "HumanEscalationNode"}
            ):
                yield {
                    "event": "PIPELINE_FINISHED",
                    "claim_id": claim_id,
                    "status": existing_checkpoint.get("status"),
                    "final_state": existing_checkpoint,
                    "idempotent": True,
                }
                return

            source_state = deepcopy(existing_checkpoint or initial_state)
            source_state["input_fingerprint"] = input_fingerprint
            current_state = self._prepare_untrusted_documents(source_state)

        yield {
            "event": "PIPELINE_STARTED",
            "claim_id": claim_id,
            "status": "in_progress",
            "message": "Initiated LangGraph state machine execution.",
            "resumed_from": current_state.get("current_node", "START"),
            "resume_mode": current_state.get("current_node", "START") not in {"", "START"},
        }

        running_state = dict(current_state)

        async for node_output in self.graph.astream(current_state):
            for node_name, node_state_diff in node_output.items():
                running_state.update(node_state_diff)
                decision = self._decision_for(node_name, running_state)
                running_state.setdefault("decision_events", []).append(decision)
                global_checkpointer.save_checkpoint(claim_id, running_state)

                yield {
                    "event": "NODE_COMPLETED",
                    "node": node_name,
                    "claim_id": claim_id,
                    "status": running_state.get("status"),
                    "current_node": node_name,
                    "state_diff": node_state_diff,
                    "execution_logs": running_state.get("execution_logs", [])[-1:] if running_state.get("execution_logs") else [],
                }
                yield {
                    "event": "DECISION_MADE",
                    "node": node_name,
                    "claim_id": claim_id,
                    "decision": decision,
                }

        yield {
            "event": "PIPELINE_FINISHED",
            "claim_id": claim_id,
            "status": running_state.get("status"),
            "final_state": running_state,
        }

    def get_pipeline_state(self, claim_id: str) -> ClaimState | None:
        """
        Retrieve stored checkpoint state for a claim.
        """
        return global_checkpointer.load_checkpoint(claim_id)
