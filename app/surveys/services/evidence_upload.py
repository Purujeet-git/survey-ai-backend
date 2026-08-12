"""
SurveyAI Backend

Module:
Survey Evidence Upload Service

Purpose:
Handles validation, metadata extraction, hashing, storage,
and database creation for uploaded survey evidence.
"""

import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.surveys.models.evidence import SurveyEvidence
from app.surveys.services.evidence import SurveyEvidenceService
from app.surveys.services.evidence_metadata import (
    EvidenceMetadataService,
)
from app.surveys.storage.local import LocalEvidenceStorage


class EvidenceUploadService:
    """
    Handles the complete survey evidence upload workflow.
    """

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        evidence_service: SurveyEvidenceService,
        storage: LocalEvidenceStorage,
        metadata_service: EvidenceMetadataService | None = None,
    ) -> None:
        self.evidence_service = evidence_service
        self.storage = storage
        self.metadata_service = (
            metadata_service
            or EvidenceMetadataService()
        )

    async def upload(
        self,
        user_id: UUID,
        survey_id: UUID,
        file: UploadFile,
    ) -> SurveyEvidence:
        """
        Validate, extract metadata, store, hash, and create
        a survey evidence record.
        """

        self._validate_content_type(
            file.content_type
        )

        file_name = Path(
            file.filename or "evidence"
        ).name

        content = await file.read()

        self._validate_file_size(
            len(content)
        )

        file_hash = hashlib.sha256(
            content
        ).hexdigest()

        metadata = self.metadata_service.extract(
            content
        )

        storage_key = await self.storage.save(
            survey_id=survey_id,
            file_name=file_name,
            content=content,
        )

        try:
            evidence = await self.evidence_service.create_evidence(
                user_id=user_id,
                survey_id=survey_id,
                evidence_type="photo",
                file_name=file_name,
                storage_key=storage_key,
                content_type=file.content_type,
                file_size=len(content),
                file_hash=file_hash,
                captured_at=metadata.get(
                    "captured_at"
                ),
                latitude=metadata.get(
                    "latitude"
                ),
                longitude=metadata.get(
                    "longitude"
                ),
                metadata_source=metadata.get(
                    "metadata_source"
                ),
                processing_status="uploaded",
                extra_data={
                    key: value
                    for key, value in metadata.items()
                    if key
                    not in {
                        "captured_at",
                        "latitude",
                        "longitude",
                        "metadata_source",
                    }
                },
            )

            return evidence

        except Exception:
            # If database creation fails after the file has
            # been stored, remove the orphaned file.
            await self.storage.delete(
                storage_key
            )

            raise

    def _validate_content_type(
        self,
        content_type: str | None,
    ) -> None:
        """
        Validate the uploaded file content type.
        """

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                "Unsupported evidence file type"
            )

    def _validate_file_size(
        self,
        file_size: int,
    ) -> None:
        """
        Validate the uploaded file size.
        """

        if file_size <= 0:
            raise ValueError(
                "Evidence file cannot be empty"
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                "Evidence file exceeds maximum size"
            )