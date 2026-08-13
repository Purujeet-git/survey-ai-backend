"""
SurveyAI Backend

Module:
Document Text & OCR Extraction Service

Purpose:
Extracts plain text content from PDFs, text files, and images.
"""

import io


class DocumentExtractionService:
    """
    Service for text & OCR extraction from documents.
    """

    def extract_text(self, content: bytes, content_type: str) -> str:
        """
        Extract text from file bytes.
        """
        if content_type == "application/pdf":
            return self._extract_pdf_text(content)
        elif content_type in {"text/plain", "text/csv", "application/json"}:
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        elif content_type.startswith("image/"):
            return self._extract_image_ocr(content)
        return ""

    def _extract_pdf_text(self, content: bytes) -> str:
        extracted_pages = []
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(f"--- Page {i+1} ---\n{text.strip()}")
        except Exception:
            pass

        return "\n\n".join(extracted_pages)

    def _extract_image_ocr(self, content: bytes) -> str:
        """
        OCR fallback for image files.
        """
        return "[Image Evidence: OCR processing ready for vision analysis]"
