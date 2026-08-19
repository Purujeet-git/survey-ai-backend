"""
SurveyAI Backend

Module:
Local Disk Storage Engine

Purpose:
Zero-cost local filesystem storage implementation.
"""

from pathlib import Path
from uuid import uuid4

import anyio

from app.config import settings
from app.storage.base import BaseStorage


class LocalDiskStorage(BaseStorage):
    """
    Local filesystem storage engine.

    Stores files inside the configured upload directory on local disk.
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(getattr(settings, "UPLOAD_DIR", "uploads")).resolve()

        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        folder: str,
        file_name: str,
        content: bytes,
    ) -> str:
        """
        Save file content locally and return relative storage key.
        """
        target_dir = self.base_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid4().hex}_{file_name}"
        file_path = target_dir / unique_filename

        async with await anyio.open_file(file_path, "wb") as f:
            await f.write(content)

        relative_key = f"{folder}/{unique_filename}"
        return relative_key

    async def get(self, storage_key: str) -> bytes:
        """
        Retrieve file content from local disk.
        """
        file_path = self.base_dir / storage_key
        if not file_path.exists():
            raise FileNotFoundError(f"Storage file '{storage_key}' not found.")

        async with await anyio.open_file(file_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_key: str) -> None:
        """
        Delete file from local disk.
        """
        file_path = self.base_dir / storage_key
        if file_path.exists():
            file_path.unlink()

    async def exists(self, storage_key: str) -> bool:
        """
        Check if file exists on local disk.
        """
        file_path = self.base_dir / storage_key
        return file_path.exists()
