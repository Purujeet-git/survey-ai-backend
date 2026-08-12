"""
Tests for the Survey Evidence upload service.
"""

import hashlib
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.surveys.services.evidence_upload import (
    EvidenceUploadService,
)
from datetime import datetime,timezone
from tests.test_evidence_metadata import create_test_image


class FakeEvidenceService:
    """
    Lightweight fake for testing the upload workflow
    without hitting the database.
    """

    def __init__(self):
        self.created_data = None

    async def create_evidence(
        self,
        user_id,
        survey_id,
        **evidence_data,
    ):
        self.created_data = {
            "user_id": user_id,
            "survey_id": survey_id,
            **evidence_data,
        }

        return self.created_data


class FakeStorage:
    """
    Lightweight fake storage for upload service tests.
    """

    def __init__(self):
        self.saved_files = {}
        self.deleted_keys = []

    async def save(
        self,
        survey_id,
        file_name,
        content,
    ):
        storage_key = (
            f"{survey_id}/{uuid4()}_{file_name}"
        )

        self.saved_files[storage_key] = content

        return storage_key

    async def delete(
        self,
        storage_key,
    ):
        self.deleted_keys.append(storage_key)
        self.saved_files.pop(
            storage_key,
            None,
        )


def make_upload_file(
    filename="vehicle-front.jpg",
    content=b"test image content",
    content_type="image/jpeg",
):
    """
    Create an UploadFile for testing.
    """

    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={
            "content-type": content_type,
        },
    )


@pytest.mark.asyncio
async def test_upload_valid_image():
    """
    Verify that a valid image is stored and an evidence
    record is created.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    user_id = uuid4()
    survey_id = uuid4()

    file = make_upload_file()

    result = await service.upload(
        user_id=user_id,
        survey_id=survey_id,
        file=file,
    )

    assert result is not None

    assert evidence_service.created_data is not None

    assert (
        evidence_service.created_data["user_id"]
        == user_id
    )

    assert (
        evidence_service.created_data["survey_id"]
        == survey_id
    )

    assert (
        evidence_service.created_data["file_name"]
        == "vehicle-front.jpg"
    )

    assert (
        evidence_service.created_data["content_type"]
        == "image/jpeg"
    )

    assert (
        evidence_service.created_data["file_size"]
        == len(b"test image content")
    )

    assert (
        evidence_service.created_data["processing_status"]
        == "uploaded"
    )


@pytest.mark.asyncio
async def test_upload_generates_sha256_hash():
    """
    Verify that the uploaded file receives the correct
    SHA-256 hash.
    """

    content = b"test image content"

    expected_hash = hashlib.sha256(
        content
    ).hexdigest()

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    file = make_upload_file(
        content=content,
    )

    await service.upload(
        user_id=uuid4(),
        survey_id=uuid4(),
        file=file,
    )

    assert (
        evidence_service.created_data["file_hash"]
        == expected_hash
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_type",
    [
        "image/jpeg",
        "image/png",
        "image/webp",
    ],
)
async def test_upload_accepts_supported_image_types(
    content_type,
):
    """
    Verify that all supported image types are accepted.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    file = make_upload_file(
        content_type=content_type,
    )

    result = await service.upload(
        user_id=uuid4(),
        survey_id=uuid4(),
        file=file,
    )

    assert result is not None


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_content_type():
    """
    Verify that unsupported file types are rejected.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    file = make_upload_file(
        filename="document.pdf",
        content=b"pdf content",
        content_type="application/pdf",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported evidence file type",
    ):
        await service.upload(
            user_id=uuid4(),
            survey_id=uuid4(),
            file=file,
        )


@pytest.mark.asyncio
async def test_upload_rejects_empty_file():
    """
    Verify that empty files are rejected.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    file = make_upload_file(
        content=b"",
    )

    with pytest.raises(
        ValueError,
        match="Evidence file cannot be empty",
    ):
        await service.upload(
            user_id=uuid4(),
            survey_id=uuid4(),
            file=file,
        )


@pytest.mark.asyncio
async def test_upload_rejects_file_over_maximum_size():
    """
    Verify that files larger than the configured limit
    are rejected.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    oversized_content = b"x" * (
        EvidenceUploadService.MAX_FILE_SIZE + 1
    )

    file = make_upload_file(
        content=oversized_content,
    )

    with pytest.raises(
        ValueError,
        match="Evidence file exceeds maximum size",
    ):
        await service.upload(
            user_id=uuid4(),
            survey_id=uuid4(),
            file=file,
        )


@pytest.mark.asyncio
async def test_upload_removes_path_components_from_filename():
    """
    Verify that directory components are not preserved
    in the uploaded filename.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    file = make_upload_file(
        filename="../../vehicle-front.jpg",
    )

    await service.upload(
        user_id=uuid4(),
        survey_id=uuid4(),
        file=file,
    )

    assert (
        evidence_service.created_data["file_name"]
        == "vehicle-front.jpg"
    )


@pytest.mark.asyncio
async def test_upload_stores_file_before_creating_evidence():
    """
    Verify that storage happens before the evidence
    database record is created.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    survey_id = uuid4()

    await service.upload(
        user_id=uuid4(),
        survey_id=survey_id,
        file=make_upload_file(),
    )

    assert len(storage.saved_files) == 1

    storage_key = next(
        iter(storage.saved_files)
    )

    assert str(survey_id) in storage_key

    assert (
        evidence_service.created_data["storage_key"]
        == storage_key
    )


@pytest.mark.asyncio
async def test_upload_cleans_storage_when_database_creation_fails():
    """
    Verify that an uploaded file is removed when evidence
    database creation fails.
    """

    class FailingEvidenceService:
        async def create_evidence(
            self,
            user_id,
            survey_id,
            **evidence_data,
        ):
            raise RuntimeError(
                "Database creation failed"
            )

    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=FailingEvidenceService(),
        storage=storage,
    )

    with pytest.raises(
        RuntimeError,
        match="Database creation failed",
    ):
        await service.upload(
            user_id=uuid4(),
            survey_id=uuid4(),
            file=make_upload_file(),
        )

    assert len(storage.saved_files) == 0
    assert len(storage.deleted_keys) == 1
    
@pytest.mark.asyncio
async def test_upload_extracts_and_stores_exif_metadata():
    """
    Verify that EXIF metadata is extracted from the uploaded
    image and passed to the evidence creation service.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    content = create_test_image(
        captured_at="2026:08:13 10:15:30",
        latitude=(28.0, 36.0, 0.0),
        latitude_ref="N",
        longitude=(77.0, 12.0, 0.0),
        longitude_ref="E",
        make="Nikon",
        model="Z8",
    )

    file = make_upload_file(
        filename="vehicle-front.jpg",
        content=content,
        content_type="image/jpeg",
    )

    user_id = uuid4()
    survey_id = uuid4()

    await service.upload(
        user_id=user_id,
        survey_id=survey_id,
        file=file,
    )

    created_data = evidence_service.created_data

    assert created_data is not None

    assert created_data["captured_at"] == datetime(
        2026,
        8,
        13,
        10,
        15,
        30,
        tzinfo=timezone.utc,
    )

    assert created_data["latitude"] == pytest.approx(
        28.6
    )

    assert created_data["longitude"] == pytest.approx(
        77.2
    )

    assert (
        created_data["metadata_source"]
        == "exif"
    )

    assert created_data["extra_data"][
        "camera_make"
    ] == "Nikon"

    assert created_data["extra_data"][
        "camera_model"
    ] == "Z8"
    
@pytest.mark.asyncio
async def test_upload_preserves_partial_exif_metadata():
    """
    Verify that valid partial EXIF metadata is preserved
    instead of being discarded.
    """

    evidence_service = FakeEvidenceService()
    storage = FakeStorage()

    service = EvidenceUploadService(
        evidence_service=evidence_service,
        storage=storage,
    )

    content = create_test_image(
        latitude=(28.0, 36.0, 0.0),
        latitude_ref="N",
    )

    file = make_upload_file(
        content=content,
    )

    await service.upload(
        user_id=uuid4(),
        survey_id=uuid4(),
        file=file,
    )

    created_data = evidence_service.created_data

    assert created_data is not None

    assert created_data["latitude"] == pytest.approx(
        28.6
    )

    assert created_data["longitude"] is None

    assert (
        created_data["metadata_source"]
        == "exif"
    )