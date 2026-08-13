"""
Test suite for Sprint 3 — Documents Subsystem:
- Zero-cost Storage Engine
- Document Metadata & Hashing
- Document Classification Engine
- OCR / Text Extraction Engine
- Versioning Service
"""

import pytest
import app.database.models  # Ensures all SQLAlchemy models are registered
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.documents.services.classification_service import DocumentClassificationService
from app.documents.services.extraction_service import DocumentExtractionService
from app.documents.services.metadata_service import DocumentMetadataService
from app.documents.services.versioning_service import DocumentVersioningService
from app.documents.models.document import Document
from app.storage.local import LocalDiskStorage


class DummyDocumentRepository:
    def __init__(self):
        self.docs = {}

    async def create(self, doc):
        if not doc.id:
            doc.id = uuid4()
        self.docs[doc.id] = doc
        return doc

    async def get_by_id(self, doc_id):
        return self.docs.get(doc_id)

    async def list_versions(self, parent_id):
        res = [
            d for d in self.docs.values()
            if d.id == parent_id or d.parent_document_id == parent_id
        ]
        return sorted(res, key=lambda x: x.version)

    async def update(self, doc):
        self.docs[doc.id] = doc
        return doc


@pytest.mark.asyncio
async def test_local_disk_storage():
    with TemporaryDirectory() as temp_dir:
        storage = LocalDiskStorage(base_dir=temp_dir)
        content = b"Sample document bytes for testing storage."

        # Save file
        key = await storage.save(folder="claims/123", file_name="test.txt", content=content)
        assert "claims/123" in key

        # Check existence
        assert await storage.exists(key) is True

        # Retrieve file
        read_bytes = await storage.get(key)
        assert read_bytes == content

        # Delete file
        await storage.delete(key)
        assert await storage.exists(key) is False


def test_document_metadata_service():
    service = DocumentMetadataService()
    content = b"PDF document sample text"

    sha256 = service.compute_sha256(content)
    assert len(sha256) == 64

    meta = service.extract_metadata(content, "text/plain")
    assert meta["file_size"] == len(content)
    assert meta["hash"] == sha256


def test_document_classification_service():
    service = DocumentClassificationService()

    # FIR classification
    doc_type, conf, _ = service.classify(file_name="Police_FIR_copy.pdf", content_type="application/pdf")
    assert doc_type == "FIR"
    assert conf > 0.5

    # Driving License classification
    doc_type, conf, _ = service.classify(file_name="Driver_License_Front.jpg", content_type="image/jpeg")
    assert doc_type == "DRIVING_LICENSE"

    # Repair Estimate
    doc_type, conf, _ = service.classify(file_name="repair_quotation_bill.pdf", content_type="application/pdf")
    assert doc_type == "REPAIR_ESTIMATE"

    # Photo fallback
    doc_type, conf, _ = service.classify(file_name="damage_side.jpg", content_type="image/jpeg")
    assert doc_type == "ACCIDENT_PHOTO"


def test_document_extraction_service():
    service = DocumentExtractionService()
    text_content = b"First Information Report\nAccident details recorded on 2026-08-13."

    extracted = service.extract_text(text_content, "text/plain")
    assert "First Information Report" in extracted


@pytest.mark.asyncio
async def test_document_versioning_service():
    repo = DummyDocumentRepository()
    service = DocumentVersioningService(repo)

    claim_id = uuid4()
    user_id = uuid4()

    # Create v1 parent doc
    parent_doc = Document(
        id=uuid4(),
        claim_id=claim_id,
        user_id=user_id,
        document_type="REPAIR_ESTIMATE",
        file_name="estimate_v1.pdf",
        storage_key="claims/1/estimate_v1.pdf",
        content_type="application/pdf",
        file_size=5000,
        file_hash="hash1",
        version=1,
        is_latest=True,
    )
    await repo.create(parent_doc)

    # Create v2 new version
    v2_doc = await service.create_new_version(
        parent_document_id=parent_doc.id,
        new_file_name="estimate_v2.pdf",
        storage_key="claims/1/estimate_v2.pdf",
        content_type="application/pdf",
        file_size=6000,
        file_hash="hash2",
    )

    assert v2_doc.version == 2
    assert v2_doc.is_latest is True
    assert parent_doc.is_latest is False
    assert v2_doc.parent_document_id == parent_doc.id

    history = await service.get_version_history(v2_doc.id)
    assert len(history) == 2
    assert [d.version for d in history] == [1, 2]
