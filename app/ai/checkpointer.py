"""
SurveyAI Backend

Module:
State Checkpointer Engine

Purpose:
Saves and retrieves ClaimState checkpoints to enable resumable AI workflow execution.
"""

import json
import os
from copy import deepcopy
from typing import Any
from app.ai.state import ClaimState

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "checkpoints")


class StateCheckpointer:
    """
    Persistent checkpointer for saving and resuming graph execution states across process restarts.
    Fulfills Floor Requirement #2: 'Kill the process in the middle of a run and start it again. It continues from where it left off.'
    """

    def __init__(self, checkpoint_dir: str = CHECKPOINT_DIR) -> None:
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self._memory_cache: dict[str, dict[str, Any]] = {}

    def _get_path(self, claim_id: str) -> str:
        safe_id = "".join(c for c in claim_id if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.checkpoint_dir, f"{safe_id}.json")

    def save_checkpoint(self, claim_id: str, state: ClaimState) -> None:
        """
        Save a snapshot of ClaimState both in memory and to disk.
        """
        snapshot = deepcopy(state)
        self._memory_cache[claim_id] = snapshot

        # Persist to disk for process kill recovery
        try:
            with open(self._get_path(claim_id), "w", encoding="utf-8") as f:
                json.dump(snapshot, f, default=str)
        except Exception:
            pass

    def load_checkpoint(self, claim_id: str) -> ClaimState | None:
        """
        Retrieve the latest snapshot of ClaimState from memory or disk.
        """
        if claim_id in self._memory_cache:
            return deepcopy(self._memory_cache[claim_id])

        filepath = self._get_path(claim_id)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memory_cache[claim_id] = data
                    return deepcopy(data)
            except Exception:
                return None

        return None

    def clear_checkpoint(self, claim_id: str) -> None:
        """
        Remove stored checkpoint from memory and disk.
        """
        self._memory_cache.pop(claim_id, None)
        filepath = self._get_path(claim_id)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


# Global checkpointer instance
global_checkpointer = StateCheckpointer()

