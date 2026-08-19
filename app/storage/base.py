"""
SurveyAI Backend

Module:
Abstract Storage Base Interface

Purpose:
Defines the abstract interface for file storage implementations (Local, S3/MinIO).
"""

from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """
    Abstract interface for object/file storage operations.
    """

    @abstractmethod
    async def save(
        self,
        folder: str,
        file_name: str,
        content: bytes,
    ) -> str:
        """
        Save file content and return unique storage key.
        """
        pass

    @abstractmethod
    async def get(self, storage_key: str) -> bytes:
        """
        Retrieve file content by storage key.
        """
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """
        Delete file from storage.
        """
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """
        Check if file exists in storage.
        """
        pass
