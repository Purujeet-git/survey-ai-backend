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
from app.ai.state import ClaimState


def build_claim_processing_graph():
    """
    Constructs the full LangGraph StateGraph workflow.
    """
    workflow = StateGraph(ClaimState)

    # Add nodes
    workflow.add_node("IntakeNode", intake_node)
    workflow.add_node("ClassificationNode", classification_node)
    workflow.add_node("ExtractionNode", extraction_node)
    workflow.add_node("AccidentUnderstandingNode", accident_understanding_node)
    workflow.add_node("PhotoAnalysisNode", photo_analysis_node)
    workflow.add_node("ExpectedDamageNode", expected_damage_node)
    workflow.add_node("EvidenceValidationNode", evidence_validation_node)
    workflow.add_node("ConflictDetectionNode", conflict_detection_node)

    # Add linear edges
    workflow.add_edge(START, "IntakeNode")
    workflow.add_edge("IntakeNode", "ClassificationNode")
    workflow.add_edge("ClassificationNode", "ExtractionNode")
    workflow.add_edge("ExtractionNode", "AccidentUnderstandingNode")
    workflow.add_edge("AccidentUnderstandingNode", "PhotoAnalysisNode")
    workflow.add_edge("PhotoAnalysisNode", "ExpectedDamageNode")
    workflow.add_edge("ExpectedDamageNode", "EvidenceValidationNode")
    workflow.add_edge("EvidenceValidationNode", "ConflictDetectionNode")
    workflow.add_edge("ConflictDetectionNode", END)

    return workflow.compile()


class ClaimAIPipelineService:
    """
    Orchestration service for executing and resuming the Claim AI Processing Pipeline.
    """

    def __init__(self) -> None:
        self.graph = build_claim_processing_graph()

    async def run_pipeline(self, initial_state: ClaimState) -> ClaimState:
        """
        Execute or resume the graph pipeline for a claim.
        """
        claim_id = initial_state.get("claim_id", "")
        existing_checkpoint = global_checkpointer.load_checkpoint(claim_id)

        current_state = existing_checkpoint or initial_state

        result_state = await self.graph.ainvoke(current_state)

        # Save latest checkpoint
        global_checkpointer.save_checkpoint(claim_id, result_state)

        return result_state

    async def astream_pipeline(self, initial_state: ClaimState):
        """
        Stream stage-by-stage node execution events for real-time UI visualization.
        """
        claim_id = initial_state.get("claim_id", "")
        existing_checkpoint = global_checkpointer.load_checkpoint(claim_id)
        current_state = existing_checkpoint or initial_state

        yield {
            "event": "PIPELINE_STARTED",
            "claim_id": claim_id,
            "status": "in_progress",
            "message": "Initiated LangGraph state machine execution.",
        }

        running_state = dict(current_state)

        async for node_output in self.graph.astream(current_state):
            for node_name, node_state_diff in node_output.items():
                running_state.update(node_state_diff)
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
