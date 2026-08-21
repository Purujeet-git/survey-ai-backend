"""
SurveyAI Backend

Module:
Model Context Protocol (MCP) Server

Purpose:
Exposes the complete SurveyAI Agentic Pipeline, Human Review Gate, and Report Generator as standard MCP tools.
Fulfills Task 1 Floor Requirement #4: 'A machine can drive it' and 'Exposing your system as an MCP server is the strongest version of behavior four.'
"""

import asyncio
import json
import sys
import os
import time
import re
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from threading import RLock
from uuid import uuid4
from typing import Any

from app.ai.security_guardrails import SecurityGuardrails
from app.ai.graph import ClaimAIPipelineService
from app.documents.services.watcher_service import IncrementalUpdateService
from app.reports.services.excel_service import ExcelAssessmentService
from app.reports.services.docx_service import WordReportService


class MCPClientError(ValueError):
    """A client supplied invalid MCP tool input."""


class SurveyAIMCPServer:
    """
    Standard MCP (Model Context Protocol) Server implementation.
    Allows Claude, Cursor, or external automated agents to drive the SurveyAI pipeline end-to-end.
    """

    TOOLS = [
        {
            "name": "claim_initialize",
            "description": "Initializes a new claim workspace or retrieves an existing claim.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_number": {"type": "string", "description": "Unique claim identifier, e.g. CLM-2026-001"},
                    "registration_number": {"type": "string", "description": "Vehicle registration number"},
                    "policy_number": {"type": "string", "description": "Insurance policy number"},
                },
                "required": ["claim_number"],
            },
        },
        {
            "name": "document_upload",
            "description": "Uploads and stages a document or photo evidence in the claim workspace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                    "file_name": {"type": "string", "description": "Name of the file"},
                    "document_type": {"type": "string", "description": "Optional category override (REPAIR_ESTIMATE, ACCIDENT_PHOTO, FIR, etc.)"},
                    "extracted_text": {"type": "string", "description": "Extracted text or OCR content"},
                },
                "required": ["claim_id", "file_name"],
            },
        },
        {
            "name": "pipeline_run",
            "description": "Executes or resumes the 8-stage LangGraph Agentic Pipeline for fact extraction, damage vision, and conflict detection.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID to process"},
                },
                "required": ["claim_id"],
            },
        },
        {
            "name": "review_get_findings",
            "description": "Retrieves itemized AI findings, detected contradictions, and review gate status.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                },
                "required": ["claim_id"],
            },
        },
        {
            "name": "review_submit_decision",
            "description": "Submits an item-level review decision (APPROVE, REJECT, EDIT) to a finding. Rejecting one finding does not discard others.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                    "finding_id": {"type": "string", "description": "Finding identifier, e.g. find-1"},
                    "action": {"type": "string", "enum": ["APPROVE", "REJECT", "EDIT"], "description": "Review decision"},
                    "comment": {"type": "string", "description": "Surveyor feedback reason or review comment"},
                    "override_value": {"type": "object", "description": "Optional override value for EDIT action"},
                },
                "required": ["claim_id", "finding_id", "action"],
            },
        },
        {
            "name": "review_commit_gate",
            "description": "Finalizes and locks the human review gate, committing decisions into the final report assessment.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                },
                "required": ["claim_id"],
            },
        },
        {
            "name": "report_export",
            "description": "Generates and exports the final survey loss assessment Excel spreadsheet (with native formulas) or Word DOCX report.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                    "format": {"type": "string", "enum": ["EXCEL", "DOCX", "ALL"], "description": "Export format"},
                },
                "required": ["claim_id"],
            },
        },
        {
            "name": "incremental_ingest",
            "description": "Performs a focused incremental update when a new document arrives mid-claim, preserving untouched state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "Target claim UUID"},
                    "file_name": {"type": "string", "description": "New document filename"},
                    "extracted_text": {"type": "string", "description": "Document text content"},
                    "content_type": {"type": "string", "description": "Optional MIME type"},
                },
                "required": ["claim_id", "file_name"],
            },
        },
    ]

    def __init__(self, store_path: str | None = None) -> None:
        self.store_path = Path(store_path or os.path.join(os.path.dirname(__file__), "..", "uploads", "mcp_claims.json")).resolve()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.claims_store: dict[str, dict[str, Any]] = self._load_store()

    def _load_store(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_store(self) -> None:
        temp = self.store_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.claims_store, default=str), encoding="utf-8")
        os.replace(temp, self.store_path)

    @contextmanager
    def _store_transaction(self):
        """Cross-instance read/modify/write transaction for the MCP store."""
        lock_path = self.store_path.with_suffix(".store-lock")
        with self._lock:
            if os.name == "nt":
                import msvcrt
                handle = open(lock_path, "a+b")
                try:
                    handle.seek(0)
                    if handle.tell() == 0:
                        handle.write(b"0")
                        handle.flush()
                    handle.seek(0)
                    while True:
                        try:
                            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                            break
                        except OSError:
                            time.sleep(0.02)
                except Exception:
                    handle.close()
                    raise
            else:
                handle = None
            self.claims_store = self._load_store()
            try:
                yield self.claims_store
                self._save_store()
            finally:
                if handle is not None:
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    handle.close()

    @asynccontextmanager
    async def _claim_lock(self, claim_id: str):
        """Serialize same-claim pipelines while keeping different claims concurrent."""
        lock_path = self.store_path.parent / f".claim-{claim_id}.lock"
        while True:
            try:
                lock_path.mkdir()
                break
            except FileExistsError:
                await asyncio.sleep(0.02)
        try:
            yield
        finally:
            try:
                lock_path.rmdir()
            except OSError:
                pass

    def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Synchronous adapter used by scripts and offline tests. The stdio server
        awaits the same real async handlers directly.
        """
        return asyncio.run(self.handle_tool_call_async(tool_name, arguments))

    @staticmethod
    def _validate_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
        if tool_name not in {tool["name"] for tool in SurveyAIMCPServer.TOOLS}:
            raise MCPClientError(f"Unknown tool: {tool_name}")
        if not isinstance(arguments, dict):
            raise MCPClientError("Tool arguments must be an object")
        required = next(tool["inputSchema"].get("required", []) for tool in SurveyAIMCPServer.TOOLS if tool["name"] == tool_name)
        missing = [field for field in required if not arguments.get(field)]
        if missing:
            raise MCPClientError(f"Missing required argument(s): {', '.join(missing)}")
        claim_id = arguments.get("claim_id")
        if claim_id is not None and (not isinstance(claim_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", claim_id)):
            raise MCPClientError("claim_id contains invalid characters")
        if tool_name == "review_submit_decision":
            if arguments.get("action") not in {"APPROVE", "REJECT", "EDIT"}:
                raise MCPClientError("action must be APPROVE, REJECT, or EDIT")
            if arguments["action"] == "EDIT" and not isinstance(arguments.get("override_value"), dict):
                raise MCPClientError("EDIT decisions require an override_value object")
        if tool_name == "report_export" and arguments.get("format", "ALL") not in {"EXCEL", "DOCX", "ALL"}:
            raise MCPClientError("format must be EXCEL, DOCX, or ALL")

    async def handle_tool_call_async(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._validate_arguments(tool_name, arguments)
        claim_id = arguments.get("claim_id", arguments.get("claim_number", ""))
        if tool_name == "claim_initialize":
            return await self._handle_tool_call_async_unlocked(tool_name, arguments)
        if tool_name in {"pipeline_run", "incremental_ingest", "document_upload", "review_submit_decision", "review_commit_gate", "review_get_findings", "report_export"}:
            async with self._claim_lock(str(claim_id)):
                with self._lock:
                    self.claims_store = self._load_store()
                return await self._handle_tool_call_async_unlocked(tool_name, arguments)
        return await self._handle_tool_call_async_unlocked(tool_name, arguments)

    async def _handle_tool_call_async_unlocked(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute machine operations against the real pipeline and artifacts."""
        claim_id = arguments.get("claim_id", arguments.get("claim_number", "default-claim"))

        if tool_name == "claim_initialize":
            claim_id = arguments.get("claim_id") or str(uuid4())
            claim_data = {
                "id": claim_id,
                "claim_number": arguments["claim_number"],
                "registration_number": arguments.get("registration_number"),
                "policy_number": arguments.get("policy_number"),
                "documents": [],
                "findings": [],
                "human_reviews": {},
                "review_committed": False,
                "status": "INITIALIZED",
            }
            with self._store_transaction():
                self.claims_store[claim_id] = claim_data
            return {"status": "SUCCESS", "claim": claim_data}

        claim = self.claims_store.get(claim_id)
        if not claim:
            return {"status": "ERROR", "message": f"Claim '{claim_id}' is not initialized."}

        if tool_name == "document_upload":
            sanitized_text, injection_detected = SecurityGuardrails.sanitize_untrusted_text(arguments.get("extracted_text", ""))
            doc = {
                "id": f"doc-{uuid4().hex[:10]}",
                "file_name": arguments["file_name"],
                "document_type": arguments.get("document_type", "OTHER"),
                "content_type": arguments.get("content_type", "text/plain"),
                "extracted_text": sanitized_text,
                "injection_detected": injection_detected,
            }
            if any(existing.get("extracted_text") == sanitized_text and existing.get("file_name") == doc["file_name"] for existing in claim.get("documents", [])):
                return {"status": "SUCCESS", "duplicate": True, "document": next(existing for existing in claim["documents"] if existing.get("file_name") == doc["file_name"] and existing.get("extracted_text") == sanitized_text), "total_documents": len(claim["documents"])}
            claim["documents"].append(doc)
            with self._store_transaction():
                self.claims_store[claim_id] = claim
            return {"status": "SUCCESS", "duplicate": False, "document": doc, "total_documents": len(claim["documents"])}

        if tool_name == "review_get_findings":
            return {"claim_id": claim_id, "findings": claim.get("findings", []), "reviews": claim.get("human_reviews", {}), "is_committed": claim.get("review_committed", False)}

        if tool_name == "review_submit_decision":
            finding_id = arguments["finding_id"]
            if not any(finding.get("id") == finding_id for finding in claim.get("findings", [])):
                return {"status": "ERROR", "message": f"Finding '{finding_id}' does not exist."}
            if claim.get("review_committed"):
                return {"status": "ERROR", "message": "Review gate is already committed and locked."}
            claim.setdefault("human_reviews", {})[finding_id] = {
                "action": arguments["action"],
                "comment": arguments.get("comment", ""),
                "override_value": arguments.get("override_value"),
            }
            with self._store_transaction():
                self.claims_store[claim_id] = claim
            return {"status": "SUCCESS", "finding_id": finding_id, "applied_action": arguments["action"], "all_reviews": claim["human_reviews"]}

        if tool_name == "review_commit_gate":
            if claim.get("review_committed"):
                return {"status": "SUCCESS", "claim_id": claim_id, "is_committed": True}
            missing = [finding.get("id") for finding in claim.get("findings", []) if finding.get("id") not in claim.get("human_reviews", {})]
            if missing:
                return {"status": "ERROR", "message": f"Every finding needs an explicit decision before commit: {missing}"}
            claim["review_committed"] = True
            claim["status"] = "GATE_COMMITTED"
            with self._store_transaction():
                self.claims_store[claim_id] = claim
            return {"status": "SUCCESS", "claim_id": claim_id, "is_committed": True}

        if tool_name == "pipeline_run":
            if not claim.get("documents"):
                return {"status": "ERROR", "message": "Cannot run pipeline without at least one uploaded document."}
            saved_state = claim.get("pipeline_state")
            state = saved_state or {
                "claim_id": claim_id,
                "claim_number": claim.get("claim_number", claim_id),
                "documents": claim["documents"],
                "execution_logs": [],
                "current_node": "START",
            }
            # A new upload is input to the next run; preserve the completed
            # state so the durable graph resumes at its next node.
            state["documents"] = claim["documents"]
            result = await ClaimAIPipelineService().run_pipeline(state)
            claim["pipeline_state"] = result
            claim["execution_logs"] = result.get("execution_logs", [])
            claim["decision_events"] = result.get("decision_events", [])
            claim["findings"] = result.get("findings", [])
            claim["status"] = result.get("status", "completed")
            with self._store_transaction():
                self.claims_store[claim_id] = claim
            return {
                "status": "SUCCESS" if result.get("status") != "awaiting_human_intervention" else "ESCALATED",
                "claim_id": claim_id,
                "current_node": result.get("current_node"),
                "nodes_executed": [log.get("node") for log in result.get("execution_logs", [])],
                "decisions": result.get("decision_events", []),
                "findings_count": len(claim["findings"]),
                "findings": claim["findings"],
            }

        if tool_name == "incremental_ingest":
            state = claim.get("pipeline_state")
            if not state:
                return {"status": "ERROR", "message": "Run the pipeline before ingesting an incremental document."}
            new_document = {
                "id": f"doc-{uuid4().hex[:10]}",
                "file_name": arguments.get("file_name"),
                "content_type": arguments.get("content_type", "text/plain"),
                "extracted_text": arguments.get("extracted_text", ""),
            }
            updated_state, delta = await IncrementalUpdateService().process_incremental_document(state, new_document)
            claim["pipeline_state"] = updated_state
            claim["documents"] = updated_state.get("documents", claim.get("documents", []))
            claim["findings"] = updated_state.get("findings", claim.get("findings", []))
            claim["status"] = "incrementally_updated"
            if delta.get("status") != "IDEMPOTENT_NOOP":
                claim["review_committed"] = False
            with self._store_transaction():
                self.claims_store[claim_id] = claim
            return {"status": "SUCCESS", "claim_id": claim_id, **delta}

        if tool_name == "report_export":
            if not claim.get("review_committed"):
                return {"status": "ERROR", "message": "Human review gate must be committed before export."}
            state = claim.get("pipeline_state", {})
            extracted = state.get("extracted_entities", {})
            claim_data = {
                "claim_number": claim.get("claim_number", claim_id),
                "policy_number": claim.get("policy_number", ""),
                "registration_number": claim.get("registration_number", ""),
                "vehicle_model": claim.get("vehicle_model", ""),
                "accident_narrative": state.get("accident_analysis", {}).get("consistency_analysis", "Grounded source summary unavailable."),
            }
            parts = extracted.get("estimate", {}).get("line_items", [])
            labor: list[dict[str, Any]] = []
            export_dir = self.store_path.parent / "mcp_exports" / str(claim_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            fmt = arguments.get("format", "ALL").upper()
            result = {"status": "SUCCESS", "claim_id": claim_id, "format": fmt, "files": []}
            if fmt in {"EXCEL", "ALL"}:
                excel = ExcelAssessmentService().generate_assessment_excel(claim_data, parts, labor)
                path = export_dir / "survey_assessment.xlsx"
                path.write_bytes(excel)
                result["files"].append({"format": "EXCEL", "path": str(path), "bytes": len(excel)})
            if fmt in {"DOCX", "ALL"}:
                docx = WordReportService().generate_survey_report_docx(claim_data, parts, labor, claim.get("findings", []))
                path = export_dir / "survey_report.docx"
                path.write_bytes(docx)
                result["files"].append({"format": "DOCX", "path": str(path), "bytes": len(docx)})
            for artifact in result["files"]:
                if artifact["format"] == "EXCEL":
                    result["excel_export_url"] = artifact["path"]
                if artifact["format"] == "DOCX":
                    result["docx_export_url"] = artifact["path"]
            return result

        return {"status": "ERROR", "message": f"Unknown async tool: {tool_name}"}

    async def run_stdio_server(self):
        """
        Runs stdio JSON-RPC loop handling MCP requests.
        """
        while True:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            if not line.strip():
                continue
            request = None
            try:
                request = json.loads(line)
                req_id = request.get("id")
                method = request.get("method")

                if request.get("jsonrpc") != "2.0" or not method:
                    raise MCPClientError("Invalid JSON-RPC request")
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {"tools": {"listChanged": False}},
                            "serverInfo": {"name": "survey-ai", "version": "1.0.0"},
                        },
                    }
                elif method == "notifications/initialized":
                    continue
                elif method == "tools/list":
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.TOOLS}}
                elif method == "tools/call":
                    params = request.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await self.handle_tool_call_async(name, arguments)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
                else:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not found"}}

                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except MCPClientError as exc:
                err_resp = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None, "error": {"code": -32602, "message": str(exc)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except Exception as exc:
                err_resp = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None, "error": {"code": -32603, "message": str(exc)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    server = SurveyAIMCPServer()
    asyncio.run(server.run_stdio_server())
