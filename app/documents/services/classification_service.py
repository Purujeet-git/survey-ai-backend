"""
SurveyAI Backend

Module:
Document Classification Service

Purpose:
Classifies uploaded claim documents into functional domain types based on filename, text content, and heuristics.
"""

import re


class DocumentClassificationService:
    """
    Automated document type classification service.
    """

    PATTERNS: dict[str, list[str]] = {
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

    def classify(self, file_name: str, content_type: str, text: str | None = None) -> tuple[str, float, str]:
        """
        Classify document type returning (type, confidence_score, explanation).
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
            return "OTHER", 0.50, "General document without matching keywords."

        confidence = min(0.95, 0.60 + (best_score * 0.05))
        return best_type, round(confidence, 2), f"Matched keywords for category '{best_type}'."
