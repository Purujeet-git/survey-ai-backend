"""
Tests for the local survey evidence storage.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from app.surveys.storage.local import LocalEvidenceStorage


@pytest.fixture
def storage(tmp_path):
    """
    Provide isolated local storage for each test.
    """

    return LocalEvidenceStorage(
        base_path=tmp_path / "evidence"
    )


@pytest.mark.asyncio
async def test_save_evidence(storage):
    """
    Verify that an evidence file can be saved.
    """

    survey_id = uuid4()

    content = b"test image content"

    storage_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-front.jpg",
        content=content,
    )

    assert storage_key is not None
    assert storage_key.endswith(".jpg")

    file_path = storage.get_path(storage_key)

    assert file_path.exists()
    assert file_path.is_file()
    assert file_path.read_bytes() == content


@pytest.mark.asyncio
async def test_save_creates_survey_directory(storage):
    """
    Verify that files are stored inside the survey-specific
    directory.
    """

    survey_id = uuid4()

    storage_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-side.jpg",
        content=b"side image",
    )

    file_path = storage.get_path(storage_key)

    assert file_path.parent.name == str(survey_id)


@pytest.mark.asyncio
async def test_exists_returns_true_for_existing_file(storage):
    """
    Verify that exists() detects a stored file.
    """

    survey_id = uuid4()

    storage_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-rear.jpg",
        content=b"rear image",
    )

    assert await storage.exists(storage_key) is True


@pytest.mark.asyncio
async def test_exists_returns_false_for_missing_file(storage):
    """
    Verify that exists() returns False for a missing file.
    """

    storage_key = "missing/evidence.jpg"

    assert await storage.exists(storage_key) is False


@pytest.mark.asyncio
async def test_get_path_returns_correct_path(storage):
    """
    Verify that get_path() resolves the storage key correctly.
    """

    storage_key = "survey-123/evidence/photo.jpg"

    path = storage.get_path(storage_key)

    assert path == (
        Path(storage.base_path)
        / "survey-123"
        / "evidence"
        / "photo.jpg"
    )


@pytest.mark.asyncio
async def test_delete_evidence(storage):
    """
    Verify that a stored evidence file can be deleted.
    """

    survey_id = uuid4()

    storage_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-damage.jpg",
        content=b"damage image",
    )

    assert await storage.exists(storage_key) is True

    await storage.delete(storage_key)

    assert await storage.exists(storage_key) is False


@pytest.mark.asyncio
async def test_delete_missing_file_does_not_fail(storage):
    """
    Verify that deleting a nonexistent file is harmless.
    """

    await storage.delete(
        "missing/evidence.jpg"
    )


@pytest.mark.asyncio
async def test_same_filename_creates_unique_storage_keys(
    storage,
):
    """
    Verify that two files with the same original filename
    receive different storage keys.
    """

    survey_id = uuid4()

    first_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-front.jpg",
        content=b"first image",
    )

    second_key = await storage.save(
        survey_id=survey_id,
        file_name="vehicle-front.jpg",
        content=b"second image",
    )

    assert first_key != second_key

    assert await storage.exists(first_key) is True
    assert await storage.exists(second_key) is True

    assert (
        storage.get_path(first_key).read_bytes()
        == b"first image"
    )

    assert (
        storage.get_path(second_key).read_bytes()
        == b"second image"
    )


@pytest.mark.asyncio
async def test_filename_path_traversal_is_removed(
    storage,
):
    """
    Verify that directory components in a filename are not
    preserved in the stored filename.
    """

    survey_id = uuid4()

    storage_key = await storage.save(
        survey_id=survey_id,
        file_name="../../malicious.jpg",
        content=b"safe content",
    )

    file_path = storage.get_path(storage_key)

    assert file_path.exists()
    assert file_path.name.endswith("_malicious.jpg")

    assert str(file_path.parent) == str(
        storage.base_path / str(survey_id)
    )