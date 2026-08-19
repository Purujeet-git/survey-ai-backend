"""
SurveyAI Backend

Module:
Local Evidence Storage

Purpose:
Stores survey evidence files on the local filesystem.
"""

from pathlib import Path
from uuid import UUID, uuid4


class LocalEvidenceStorage:
    """
    Local filesystem storage for survey evidence.
    """

    def __init__(self, base_path: str | Path = "uploads/evidence"):
        self.base_path = Path(base_path)

    async def save(
        self,
        survey_id: UUID,
        file_name: str,
        content: bytes,
    ) -> str:
        """
        Save an evidence file and return its storage key.
        """

        survey_directory = (
            self.base_path / str(survey_id)
        )

        survey_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        storage_name = (
            f"{uuid4()}_{Path(file_name).name}"
        )

        file_path = survey_directory / storage_name

        file_path.write_bytes(content)

        return str(
            file_path.relative_to(self.base_path)
        )

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        """
        Delete a stored evidence file.
        """

        file_path = self.base_path / storage_key

        if file_path.exists():
            file_path.unlink()

    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        """
        Check whether a stored evidence file exists.
        """

        file_path = self.base_path / storage_key

        return file_path.exists()

    def get_path(
        self,
        storage_key: str,
    ) -> Path:
        """
        Return the filesystem path for a storage key.
        """

        return self.base_path / storage_key