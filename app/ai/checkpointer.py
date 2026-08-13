"""
SurveyAI Backend

Module:
State Checkpointer Engine

Purpose:
Saves and retrieves ClaimState checkpoints to enable resumable AI workflow execution.
"""

from copy import deepcopy
from app.ai.state import ClaimState


class StateCheckpointer:
    """
    In-memory / Persistent checkpointer for saving and resuming graph execution states.
    """

    def __init__(self) -> None:
        self._checkpoints: dict[str, dict[str, Any]] = {}

    def save_checkpoint(self, claim_id: str, state: ClaimState) -> None:
        """
        Save a snapshot of ClaimState for a claim.
        """
        self._checkpoints[claim_id] = deepcopy(state)

    def load_checkpoint(self, claim_id: str) -> ClaimState | None:
        """
        Retrieve the latest snapshot of ClaimState for a claim.
        """
        checkpoint = self._checkpoints.get(claim_id)
        if checkpoint:
            return deepcopy(checkpoint)
        return None

    def clear_checkpoint(self, claim_id: str) -> None:
        """
        Remove stored checkpoint.
        """
        self._checkpoints.pop(claim_id, None)


# Global checkpointer instance
global_checkpointer = StateCheckpointer()
