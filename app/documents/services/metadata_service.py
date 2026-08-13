"""
SurveyAI Backend

Module:
Document Metadata Extraction Service

Purpose:
Extracts metadata, EXIF, GPS coordinates, PDF info, and SHA256 hashes from file content.
"""

import hashlib
import io
from datetime import datetime, timezone

from PIL import Image, ExifTags


class DocumentMetadataService:
    """
    Service for extracting technical file metadata.
    """

    def compute_sha256(self, content: bytes) -> str:
        """
        Compute SHA256 hash of file content.
        """
        return hashlib.sha256(content).hexdigest()

    def extract_metadata(self, content: bytes, content_type: str) -> dict:
        """
        Extract content-type specific metadata.
        """
        metadata = {
            "file_size": len(content),
            "content_type": content_type,
            "hash": self.compute_sha256(content),
        }

        if content_type.startswith("image/"):
            img_metadata = self._extract_image_exif(content)
            metadata.update(img_metadata)
        elif content_type == "application/pdf":
            pdf_metadata = self._extract_pdf_info(content)
            metadata.update(pdf_metadata)

        return metadata

    def _extract_image_exif(self, content: bytes) -> dict:
        result = {}
        try:
            image = Image.open(io.BytesIO(content))
            result["dimensions"] = {"width": image.width, "height": image.height}
            result["format"] = image.format

            exif_raw = image._getexif()
            if not exif_raw:
                return result

            exif_data = {
                ExifTags.TAGS.get(tag, str(tag)): value
                for tag, value in exif_raw.items()
            }

            if "DateTimeOriginal" in exif_data:
                dt_str = exif_data["DateTimeOriginal"]
                try:
                    dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    result["captured_at"] = dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    pass

            gps_info = exif_data.get("GPSInfo")
            if gps_info:
                lat, lon = self._parse_gps(gps_info)
                if lat is not None and lon is not None:
                    result["latitude"] = lat
                    result["longitude"] = lon
                    result["has_location"] = True

            if "Make" in exif_data:
                result["camera_make"] = str(exif_data["Make"]).strip()
            if "Model" in exif_data:
                result["camera_model"] = str(exif_data["Model"]).strip()

        except Exception:
            pass

        return result

    def _parse_gps(self, gps_info: dict) -> tuple[float | None, float | None]:
        try:
            lat = self._convert_to_degrees(gps_info.get(2))
            if gps_info.get(1) == "S":
                lat = -lat

            lon = self._convert_to_degrees(gps_info.get(4))
            if gps_info.get(3) == "W":
                lon = -lon

            return lat, lon
        except Exception:
            return None, None

    def _convert_to_degrees(self, value) -> float:
        if not value:
            return 0.0
        d, m, s = value
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)

    def _extract_pdf_info(self, content: bytes) -> dict:
        result = {"page_count": 1}
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            result["page_count"] = len(reader.pages)
            if reader.metadata:
                if reader.metadata.title:
                    result["title"] = reader.metadata.title
                if reader.metadata.author:
                    result["author"] = reader.metadata.author
        except Exception:
            pass

        return result
