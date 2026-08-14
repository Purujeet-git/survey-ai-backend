"""
SurveyAI Backend

Module:
Document Classification Service

Purpose:
Classifies uploaded claim documents into functional domain types based on filename, text content, and heuristics.
"""

import re
import httpx
from app.config.settings import settings


class DocumentClassificationService:
    """
    Automated document type classification service with dual-mode intelligence:
    1. Gemini LLM multimodal classification when GEMINI_API_KEY is configured.
    2. Deterministic fast keyword heuristic matching as instant fallback & offline testing.
    """

    PATTERNS: dict[str, list[str]] = {
        "REPORT_TEMPLATE": [
            r"template",
            r"format",
            r"master",
            r"boilerplate",
            r"survey_report_template",
            r"sample_report",
            r"assessment_template",
        ],
        "FIR": [
            r"fir",
            r"police",
            r"first information report",
            r"thana",
            r"station house officer",
        ],
        "DRIVING_LICENSE": [
            r"dl",
            r"license",
            r"licence",
            r"driving",
            r"driver",
            r"transport authority",
            r"rto",
        ],
        "REGISTRATION_CERTIFICATE": [
            r"rc",
            r"registration",
            r"chassis",
            r"engine no",
            r"owner name",
            r"veh reg",
        ],
        "REPAIR_ESTIMATE": [
            r"estimate",
            r"quotation",
            r"bill",
            r"invoice",
            r"workshop",
            r"garage",
            r"repair",
            r"labor charge",
            r"spare part",
        ],
        "POLICY_SCHEDULE": [
            r"policy",
            r"insurance",
            r"premium",
            r"sum insured",
            r"policyholder",
        ],
        "ACCIDENT_PHOTO": [
            r"damage",
            r"photo",
            r"img",
            r"pic",
            r"crash",
            r"front",
            r"rear",
            r"side",
            r"scratch",
        ],
        "INSPECTION_NOTE": [
            r"survey",
            r"inspection",
            r"spot",
            r"note",
            r"observation",
        ],
    }

    async def classify_with_gemini(
        self, file_name: str, content_type: str, text: str | None = None
    ) -> tuple[str, float, str] | None:
        """
        Attempts semantic classification using Google Gemini LLM.
        Returns (doc_type, confidence, explanation) or None on failure.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return None

        prompt = (
            "You are an expert insurance claim surveyor AI. Classify the following document into exactly one of these categories:\n"
            "- REPORT_TEMPLATE (A word docx or excel template used to generate final survey reports)\n"
            "- REPAIR_ESTIMATE (Garage estimate, parts & labor bill/quotation)\n"
            "- ACCIDENT_PHOTO (Vehicle damage photo)\n"
            "- FIR (Police First Information Report)\n"
            "- DRIVING_LICENSE (Driver license document)\n"
            "- REGISTRATION_CERTIFICATE (Vehicle registration certificate / RC)\n"
            "- POLICY_SCHEDULE (Insurance policy schedule or cover note)\n"
            "- INSPECTION_NOTE (Surveyor on-site inspection note)\n"
            "- OTHER (General document)\n\n"
            f"File Name: {file_name}\n"
            f"Content-Type: {content_type}\n"
            f"Snippet / Extracted Text:\n{text[:1500] if text else 'None'}\n\n"
            "Respond in pure JSON format with keys: 'classified_type', 'confidence' (float 0.0-1.0), and 'explanation' (string)."
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    import json
                    text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_resp)
                    return (
                        parsed.get("classified_type", "OTHER"),
                        float(parsed.get("confidence", 0.95)),
                        parsed.get("explanation", "Classified by Gemini AI agent."),
                    )
        except Exception:
            pass

        return None

    def classify(self, file_name: str, content_type: str, text: str | None = None) -> tuple[str, float, str]:
        """
        Classify document type using deterministic heuristics returning (type, confidence_score, explanation).
        """
        combined_target = f"{file_name} {text or ''}".lower()

        scores: dict[str, int] = {doc_type: 0 for doc_type in self.PATTERNS}

        for doc_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_target, re.IGNORECASE):
                    scores[doc_type] += 2

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score == 0:
            if content_type.startswith("image/"):
                return "ACCIDENT_PHOTO", 0.70, "Identified as photo image based on MIME type."
            if file_name.endswith(".docx") and "template" in file_name.lower():
                return "REPORT_TEMPLATE", 0.90, "Identified as report template based on file extension."
            return "OTHER", 0.50, "General document without matching keywords."

        confidence = min(0.95, 0.60 + (best_score * 0.05))
        return best_type, round(confidence, 2), f"Matched keywords for category '{best_type}'."
