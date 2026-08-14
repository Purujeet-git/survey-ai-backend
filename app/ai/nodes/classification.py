"""
SurveyAI Backend

Module:
Semantic Classification Node

Purpose:
LLM agent node performing semantic classification across all uploaded claim documents.
"""

from datetime import datetime, timezone
import time
from app.ai.state import ClaimState, ExecutionLogItem
from app.documents.services.classification_service import DocumentClassificationService


async def classification_node(state: ClaimState) -> dict:
    """
    Classification Agent Node: Categorizes claim documents semantically.
    """
    start_time = time.time()
    classifier = DocumentClassificationService()

    documents = state.get("documents", [])
    results = {}

    for doc in documents:
        doc_id = doc.get("id", "unknown")
        file_name = doc.get("file_name", "")
        content_type = doc.get("content_type", "")
        text = doc.get("extracted_text", "")

        gemini_result = await classifier.classify_with_gemini(
            file_name=file_name,
            content_type=content_type,
            text=text,
        )

        if gemini_result:
            doc_type, confidence, explanation = gemini_result
        else:
            doc_type, confidence, explanation = classifier.classify(
                file_name=file_name,
                content_type=content_type,
                text=text,
            )

        results[doc_id] = {
            "file_name": file_name,
            "classified_type": doc_type,
            "confidence": confidence,
            "explanation": explanation,
        }

    latency = round((time.time() - start_time) * 1000, 2)

    log_entry: ExecutionLogItem = {
        "node": "ClassificationNode",
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency,
        "token_usage": {"input": 150 * len(documents), "output": 50 * len(documents)},
        "details": f"Classified {len(documents)} document(s).",
    }

    return {
        "classification_results": results,
        "status": "classification_completed",
        "current_node": "ClassificationNode",
        "execution_logs": [log_entry],
    }
