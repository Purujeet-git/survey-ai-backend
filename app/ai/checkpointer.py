"""
SurveyAI Backend

Module:
State Checkpointer Engine

Purpose:
Saves and retrieves ClaimState checkpoints to enable resumable AI workflow execution.
"""

import json
import os
import tempfile
from threading import RLock
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
        self._lock = RLock()

    def _get_path(self, claim_id: str) -> str:
        safe_id = "".join(c for c in claim_id if c.isalnum() or c in ("-", "_"))
        if not safe_id:
            raise ValueError("claim_id must contain at least one alphanumeric character")
        return os.path.join(self.checkpoint_dir, f"{safe_id}.json")

    def save_checkpoint(self, claim_id: str, state: ClaimState) -> None:
        """
        Save a snapshot of ClaimState both in memory and to disk.
        """
        snapshot = deepcopy(state)
        with self._lock:
            self._memory_cache[claim_id] = snapshot
            target = self._get_path(claim_id)
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix=".checkpoint-", suffix=".tmp", dir=self.checkpoint_dir)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, default=str)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, target)
            except Exception:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise

    def load_checkpoint(self, claim_id: str) -> ClaimState | None:
        """
        Retrieve the latest snapshot of ClaimState from memory or disk.
        """
        with self._lock:
            if claim_id in self._memory_cache:
                return deepcopy(self._memory_cache[claim_id])

        filepath = self._get_path(claim_id)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    with self._lock:
                        self._memory_cache[claim_id] = data
                        return deepcopy(data)
            except Exception:
                return None

        return None

    def clear_checkpoint(self, claim_id: str) -> None:
        """
        Remove stored checkpoint from memory and disk.
        """
        with self._lock:
            self._memory_cache.pop(claim_id, None)
        filepath = self._get_path(claim_id)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


# Global checkpointer instance
global_checkpointer = StateCheckpointer()
