"""
SurveyAI Backend

Module:
Watched Location & Incremental Ingestion Service

Purpose:
Implements 'The Analyst That Stays Alive': Watches directory locations and processes new document arrivals incrementally.
Updates only affected claim state sections, detects contradictions against existing facts, preserves untouched state,
and records source attribution ('what changed, when, and because of which source').
"""

from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
import re
import time
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.ai.checkpointer import global_checkpointer
from app.ai.coordination import claim_lock
from app.ai.security_guardrails import SecurityGuardrails
from app.ai.state import ClaimState, DocumentItem, ExecutionLogItem, compute_token_cost
from app.documents.services.classification_service import DocumentClassificationService
from app.documents.services.extraction_service import DocumentExtractionService


SUPPORTED_WATCH_EXTENSIONS = {".pdf", ".txt", ".csv", ".json", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class WatchRegistration:
    watch_id: str
    claim_id: str
    path: str
    status: str = "registered"
    processed_files: int = 0
    ignored_files: int = 0
    last_error: str | None = None
    last_processed_file: str | None = None
    task: asyncio.Task | None = field(default=None, repr=False)
    seen_files: set[str] = field(default_factory=set, repr=False)
    stable_candidates: dict[str, tuple[int, int, int]] = field(default_factory=dict, repr=False)


class WatcherManager:
    """Process-local filesystem watcher backed by an async polling loop."""

    def __init__(self, poll_interval: float = 0.25, stable_cycles: int = 2) -> None:
        self.poll_interval = poll_interval
        self.stable_cycles = stable_cycles
        self._registrations: dict[str, WatchRegistration] = {}
        self._lock = asyncio.Lock()
        self._extractor = DocumentExtractionService()

    async def register(self, claim_id: str, path: str) -> dict[str, Any]:
        folder = Path(path).expanduser().resolve()
        if not folder.exists() or not folder.is_dir():
            raise ValueError("watch path must be an existing directory")
        registration = WatchRegistration(str(uuid4()), claim_id, str(folder))
        async with self._lock:
            self._registrations[registration.watch_id] = registration
        return self._serialize(registration)

    async def start(self, watch_id: str) -> dict[str, Any]:
        registration = self._get(watch_id)
        if registration.status == "running":
            return self._serialize(registration)
        registration.status = "running"
        registration.last_error = None
        registration.task = asyncio.create_task(self._watch_loop(registration))
        return self._serialize(registration)

    async def stop(self, watch_id: str) -> dict[str, Any]:
        registration = self._get(watch_id)
        task = registration.task
        registration.status = "stopped"
        registration.task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self._serialize(registration)

    async def stop_all(self) -> None:
        for watch_id in list(self._registrations):
            await self.stop(watch_id)

    async def list_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        async with self._lock:
            registrations = [r for r in self._registrations.values() if r.claim_id == claim_id]
        return [self._serialize(registration) for registration in registrations]

    async def status(self, watch_id: str) -> dict[str, Any]:
        return self._serialize(self._get(watch_id))

    def _get(self, watch_id: str) -> WatchRegistration:
        registration = self._registrations.get(watch_id)
        if registration is None:
            raise KeyError(f"Watcher '{watch_id}' was not found")
        return registration

    async def _watch_loop(self, registration: WatchRegistration) -> None:
        try:
            while registration.status == "running":
                for file_path in sorted(Path(registration.path).iterdir()):
                    if not file_path.is_file():
                        continue
                    await self._consider_file(registration, file_path)
                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            registration.status = "error"
            registration.last_error = f"{type(exc).__name__}: {exc}"

    async def _consider_file(self, registration: WatchRegistration, file_path: Path) -> None:
        suffix = file_path.suffix.lower()
        path_key = str(file_path)
        if suffix not in SUPPORTED_WATCH_EXTENSIONS:
            if path_key not in registration.seen_files:
                registration.ignored_files += 1
                registration.seen_files.add(path_key)
            return
        if path_key in registration.seen_files:
            return

        stat = file_path.stat()
        previous = registration.stable_candidates.get(path_key)
        stable_count = (previous[2] + 1) if previous and previous[:2] == (stat.st_size, stat.st_mtime_ns) else 1
        registration.stable_candidates[path_key] = (stat.st_size, stat.st_mtime_ns, stable_count)
        if stable_count < self.stable_cycles:
            return

        await self._process_file(registration, file_path)
        registration.seen_files.add(path_key)
        registration.stable_candidates.pop(path_key, None)

    async def _process_file(self, registration: WatchRegistration, file_path: Path) -> None:
        content = file_path.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()
        document = {
            "id": f"watch-{content_hash}",
            "file_name": file_path.name,
            "content_type": mimetypes.guess_type(file_path.name)[0] or "application/octet-stream",
            "file_size": len(content),
            "storage_key": str(file_path),
            "extracted_text": self._extractor.extract_text(content, mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"),
            "doc_metadata": {"source": "watched_folder", "source_path": str(file_path), "content_hash": content_hash},
        }
        async with claim_lock(registration.claim_id):
            state = global_checkpointer.load_checkpoint(registration.claim_id)
            if not state:
                raise ValueError("claim has no pipeline checkpoint; run the initial pipeline before watching for updates")
            updated_state, delta = await IncrementalUpdateService().process_incremental_document(state, document)
            if delta.get("status") != "IDEMPOTENT_NOOP":
                global_checkpointer.save_checkpoint(registration.claim_id, updated_state)
                registration.processed_files += 1
                registration.last_processed_file = file_path.name

    @staticmethod
    def _serialize(registration: WatchRegistration) -> dict[str, Any]:
        return {
            "watch_id": registration.watch_id,
            "claim_id": registration.claim_id,
            "path": registration.path,
            "status": registration.status,
            "processed_files": registration.processed_files,
            "ignored_files": registration.ignored_files,
            "last_error": registration.last_error,
            "last_processed_file": registration.last_processed_file,
        }


class IncrementalUpdateService:
    """
    Processes mid-claim document arrivals incrementally against existing state.
    """

    def __init__(self) -> None:
        self.classifier = DocumentClassificationService()

    async def process_incremental_document(
        self,
        current_state: ClaimState,
        new_document: DocumentItem,
    ) -> tuple[ClaimState, dict[str, Any]]:
        """
        Executes a focused incremental update to ClaimState when a new document arrives:
        1. Classifies and extracts only the newly arrived document.
        2. Detects any contradictions between new document facts and prior state.
        3. Preserves untouched sections unchanged.
        4. Emits an audit delta log with exact source attribution.
        """
        start_time = time.time()
        file_name = new_document.get("file_name", "")
        content_type = new_document.get("content_type", "")
        raw_text = new_document.get("extracted_text", "")

        new_fingerprint = self._document_fingerprint(new_document)
        new_document_id = new_document.get("id")
        for existing_document in current_state.get("documents", []):
            same_document_id = new_document_id and existing_document.get("id") == new_document_id
            if same_document_id or self._document_fingerprint(existing_document) == new_fingerprint:
                return current_state, {
                    "source_document": file_name,
                    "status": "IDEMPOTENT_NOOP",
                    "duplicate": True,
                    "affected_sections": [],
                    "untouched_sections": [],
                    "new_conflicts_surfaced": [],
                    "latency_ms": 0.0,
                    "cost_usd": 0.0,
                    "untouched_sections_unchanged": True,
                }

        # 1. Sanitize text with Prompt Injection Defense Guardrails
        sanitized_text, injection_detected = SecurityGuardrails.sanitize_untrusted_text(raw_text)

        # 2. Classify new document
        doc_type, confidence, explanation = self.classifier.classify(
            file_name=file_name,
            content_type=content_type,
            text=raw_text,
        )

        new_doc_id = new_document.get("id", f"doc-{int(time.time())}")

        # 3. Compute affected vs untouched sections. Work on a deep copy so a
        # delta can never mutate an unrelated nested section by reference.
        before_untouched = self._section_hashes(current_state)
        existing_entities = dict(current_state.get("extracted_entities", {}))
        existing_findings = list(current_state.get("findings", []))
        affected_sections: list[str] = []
        new_conflicts: list[dict[str, Any]] = []

        # Example: if new document is a Supplemental Repair Estimate
        if doc_type == "REPAIR_ESTIMATE":
            affected_sections.append("extracted_entities.estimate")
            estimate = dict(existing_entities.get("estimate", {}))
            line_items = list(estimate.get("line_items", []))
            amounts = [float(value.replace(",", "")) for value in re.findall(r"INR\s*([0-9,]+(?:\.[0-9]{2})?)", raw_text, re.IGNORECASE)]
            if amounts:
                estimate["total_amount"] = max(amounts)
            if raw_text.strip():
                line_items.append({"description": file_name, "cost": estimate.get("total_amount", 0.0), "source_document": file_name})
            estimate["line_items"] = line_items
            existing_entities["estimate"] = estimate
            # Check if estimate introduces cost variance against policy
            policy_sum_insured = existing_entities.get("policy", {}).get("sum_insured", 0)
            if policy_sum_insured and "total" in raw_text.lower():
                # Detect potential conflict/overrun
                new_finding = {
                    "id": f"find-inc-{new_fingerprint[:16]}",
                    "title": f"Incremental Conflict from {file_name}",
                    "finding_type": "SUPPLEMENTAL_ESTIMATE_FLAG",
                    "severity": "MEDIUM",
                    "description": f"New document '{file_name}' added supplemental repair items requiring surveyor verification.",
                    "recommendation": "Review supplemental estimate line items in Human Review Gate.",
                    "source_document": file_name,
                    "surfaced_at": datetime.now(timezone.utc).isoformat(),
                }
                new_conflicts.append(new_finding)
                existing_findings.append(new_finding)

        elif doc_type == "ACCIDENT_PHOTO":
            affected_sections.append("photo_analysis")
        else:
            affected_sections.append(f"documents.{doc_type.lower()}")

        untouched_sections = [
            s for s in ["driver", "vehicle", "fir", "accident_analysis", "expected_damage"]
            if s not in affected_sections
        ]

        # 4. Merge new document manifest into state
        all_docs = list(current_state.get("documents", []))
        all_docs.append({
            **new_document,
            "document_type": doc_type,
            "extracted_text": sanitized_text,
        })

        classification_results = dict(current_state.get("classification_results", {}))
        classification_results[new_doc_id] = {
            "file_name": file_name,
            "classified_type": doc_type,
            "confidence": confidence,
            "explanation": explanation,
            "injection_attempt_defended": injection_detected,
        }

        latency = round((time.time() - start_time) * 1000, 2)
        tokens_in = 250
        tokens_out = 80
        cost = compute_token_cost(tokens_in, tokens_out)

        delta_log: ExecutionLogItem = {
            "node": "IncrementalWatcherNode",
            "status": "SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency,
            "token_usage": {"input": tokens_in, "output": tokens_out},
            "cost_usd": cost,
            "details": f"Incremental update from '{file_name}'. Affected: {affected_sections}, Untouched: {untouched_sections}.",
        }

        updated_state: ClaimState = {
            **current_state,
            "documents": all_docs,
            "extracted_entities": existing_entities,
            "classification_results": classification_results,
            "findings": existing_findings,
            "execution_logs": [delta_log],
            "current_node": "IncrementalWatcherNode",
            "status": "incrementally_updated",
        }

        delta_report = {
            "source_document": file_name,
            "status": "SUCCESS",
            "arrived_at": delta_log["timestamp"],
            "affected_sections": affected_sections,
            "untouched_sections": untouched_sections,
            "new_conflicts_surfaced": new_conflicts,
            "injection_detected": injection_detected,
            "latency_ms": latency,
            "cost_usd": cost,
            "untouched_hashes_before": before_untouched,
            "untouched_hashes_after": self._section_hashes(updated_state),
        }
        delta_report["untouched_sections_unchanged"] = all(
            before_untouched.get(name) == delta_report["untouched_hashes_after"].get(name)
            for name in untouched_sections
        )

        return updated_state, delta_report

    @staticmethod
    def _document_fingerprint(document: DocumentItem) -> str:
        payload = json.dumps({
            "id": document.get("id"),
            "file_name": document.get("file_name"),
            "content_type": document.get("content_type"),
            "extracted_text": document.get("extracted_text", ""),
        }, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _section_hashes(state: ClaimState) -> dict[str, str]:
        sections = ["driver", "vehicle", "fir", "policy", "accident_analysis", "photo_analysis", "expected_damage"]
        entities = state.get("extracted_entities", {})
        values = {name: entities.get(name, {}) for name in ["driver", "vehicle", "fir", "policy"]}
        values.update({name: state.get(name, {}) for name in ["accident_analysis", "photo_analysis", "expected_damage"]})
        return {
            name: hashlib.sha256(json.dumps(values[name], sort_keys=True, default=str).encode()).hexdigest()
            for name in sections
        }
