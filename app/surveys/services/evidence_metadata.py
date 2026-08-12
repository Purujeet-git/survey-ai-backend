"""
SurveyAI Backend

Module:
Survey Evidence Metadata Service

Purpose:
Extracts metadata from survey evidence images.
"""

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from PIL import ExifTags, Image


class EvidenceMetadataService:
    """
    Extract metadata from survey evidence images.
    """

    def extract(
        self,
        content: bytes,
    ) -> dict[str, Any]:
        """
        Extract metadata from image bytes.

        Returns a dictionary containing metadata that
        could be extracted from the image.
        """

        metadata: dict[str, Any] = {}

        try:
            image = Image.open(
                BytesIO(content)
            )

            exif = image.getexif()

            if not exif:
                return metadata

            captured_at = self._extract_capture_time(
                exif
            )

            if captured_at is not None:
                metadata["captured_at"] = captured_at

            latitude, longitude = (
                self._extract_gps(exif)
            )

            if latitude is not None:
                metadata["latitude"] = latitude

            if longitude is not None:
                metadata["longitude"] = longitude

            camera_make = self._get_exif_value(
                exif,
                "Make",
            )

            if camera_make is not None:
                metadata["camera_make"] = camera_make

            camera_model = self._get_exif_value(
                exif,
                "Model",
            )

            if camera_model is not None:
                metadata["camera_model"] = camera_model

            if metadata:
                metadata["metadata_source"] = "exif"

            return metadata

        except Exception:
            """
            Metadata extraction must never prevent the
            evidence file from being uploaded.
            """

            return {}

    def _get_exif_value(
        self,
        exif,
        tag_name: str,
    ) -> Any:
        """
        Retrieve a top-level EXIF value by tag name.
        """

        for tag_id, value in exif.items():
            decoded_tag = ExifTags.TAGS.get(
                tag_id,
                tag_id,
            )

            if decoded_tag == tag_name:
                return value

        return None

    def _extract_capture_time(
        self,
        exif,
    ) -> datetime | None:
        """
        Extract the original capture timestamp from
        the EXIF sub-IFD.
        """

        try:
            exif_ifd = exif.get_ifd(
                ExifTags.IFD.Exif
            )

        except Exception:
            return None

        value = exif_ifd.get(
            ExifTags.Base.DateTimeOriginal
        )

        if value is None:
            return None

        if isinstance(value, bytes):
            value = value.decode(
                "utf-8",
                errors="ignore",
            )

        if not isinstance(value, str):
            return None

        try:
            return datetime.strptime(
                value,
                "%Y:%m:%d %H:%M:%S",
            ).replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            return None

    def _extract_gps(
        self,
        exif,
    ) -> tuple[float | None, float | None]:
        """
        Extract latitude and longitude from the
        EXIF GPS sub-IFD.
        """

        try:
            gps_info = exif.get_ifd(
                ExifTags.IFD.GPSInfo
            )

        except Exception:
            return None, None

        if not gps_info:
            return None, None

        latitude = self._convert_gps_coordinate(
            gps_info.get(
                ExifTags.GPS.GPSLatitude
            ),
            gps_info.get(
                ExifTags.GPS.GPSLatitudeRef
            ),
        )

        longitude = self._convert_gps_coordinate(
            gps_info.get(
                ExifTags.GPS.GPSLongitude
            ),
            gps_info.get(
                ExifTags.GPS.GPSLongitudeRef
            ),
        )

        return latitude, longitude

    def _convert_gps_coordinate(
        self,
        coordinate,
        reference,
    ) -> float | None:
        """
        Convert EXIF GPS degrees/minutes/seconds into
        decimal degrees.
        """

        if not coordinate or not reference:
            return None

        try:
            if isinstance(reference, bytes):
                reference = reference.decode(
                    "ascii",
                    errors="ignore",
                )

            degrees = float(
                coordinate[0]
            )

            minutes = float(
                coordinate[1]
            )

            seconds = float(
                coordinate[2]
            )

            decimal = (
                degrees
                + minutes / 60
                + seconds / 3600
            )

            if reference in ("S", "W"):
                decimal *= -1

            return decimal

        except (
            TypeError,
            ValueError,
            IndexError,
            ZeroDivisionError,
        ):
            return None