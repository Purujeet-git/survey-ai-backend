"""
Tests for the Survey Evidence metadata service.
"""

from datetime import datetime, timezone
from io import BytesIO

import pytest
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from app.surveys.services.evidence_metadata import (
    EvidenceMetadataService,
)

def create_test_image(
    *,
    captured_at: str | None = None,
    latitude: tuple[float, float, float] | None = None,
    latitude_ref: str | None = None,
    longitude: tuple[float, float, float] | None = None,
    longitude_ref: str | None = None,
    make: str | None = None,
    model: str | None = None,
) -> bytes:
    """
    Create a real JPEG image with EXIF metadata.
    """

    image = Image.new(
        "RGB",
        (100, 100),
        color="white",
    )

    zeroth_ifd = {}
    exif_ifd = {}
    gps_ifd = {}

    if make is not None:
        zeroth_ifd[
            piexif.ImageIFD.Make
        ] = make

    if model is not None:
        zeroth_ifd[
            piexif.ImageIFD.Model
        ] = model

    if captured_at is not None:
        exif_ifd[
            piexif.ExifIFD.DateTimeOriginal
        ] = captured_at

    if latitude is not None and latitude_ref is not None:
        gps_ifd[
            piexif.GPSIFD.GPSLatitudeRef
        ] = latitude_ref

        gps_ifd[
            piexif.GPSIFD.GPSLatitude
        ] = tuple(
            (int(value), 1)
            for value in latitude
        )

    if longitude is not None and longitude_ref is not None:
        gps_ifd[
            piexif.GPSIFD.GPSLongitudeRef
        ] = longitude_ref

        gps_ifd[
            piexif.GPSIFD.GPSLongitude
        ] = tuple(
            (int(value), 1)
            for value in longitude
        )

    exif_dict = {
        "0th": zeroth_ifd,
        "Exif": exif_ifd,
        "GPS": gps_ifd,
        "1st": {},
        "thumbnail": None,
    }

    exif_bytes = piexif.dump(
        exif_dict
    )

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        exif=exif_bytes,
    )

    return output.getvalue()

@pytest.fixture
def service():
    """
    Provide an EvidenceMetadataService.
    """

    return EvidenceMetadataService()


def test_extract_returns_empty_metadata_without_exif(
    service,
):
    """
    Verify that an image without EXIF metadata returns
    an empty metadata dictionary.
    """

    image = Image.new(
        "RGB",
        (100, 100),
        color="white",
    )

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
    )

    metadata = service.extract(
        output.getvalue()
    )

    assert metadata == {}


def test_extract_capture_time(service):
    """
    Verify that DateTimeOriginal is extracted correctly.
    """

    content = create_test_image(
        captured_at="2026:08:13 14:30:45",
    )

    metadata = service.extract(content)

    assert metadata["captured_at"] == datetime(
        2026,
        8,
        13,
        14,
        30,
        45,
        tzinfo=timezone.utc,
    )

    assert metadata["metadata_source"] == "exif"


def test_extract_camera_make_and_model(service):
    """
    Verify that camera make and model are extracted.
    """

    content = create_test_image(
        make="Canon",
        model="EOS R5",
    )

    metadata = service.extract(content)

    assert metadata["camera_make"] == "Canon"
    assert metadata["camera_model"] == "EOS R5"
    assert metadata["metadata_source"] == "exif"


def test_extract_northern_eastern_gps_coordinates(
    service,
):
    """
    Verify conversion of northern/eastern GPS coordinates.
    """

    content = create_test_image(
        latitude=(28.0, 36.0, 0.0),
        latitude_ref="N",
        longitude=(77.0, 12.0, 0.0),
        longitude_ref="E",
    )

    metadata = service.extract(content)

    assert metadata["latitude"] == pytest.approx(28.6)
    assert metadata["longitude"] == pytest.approx(77.2)
    assert metadata["metadata_source"] == "exif"


def test_extract_southern_western_gps_coordinates(
    service,
):
    """
    Verify conversion of southern/western GPS coordinates.
    """

    content = create_test_image(
        latitude=(33.0, 52.0, 0.0),
        latitude_ref="S",
        longitude=(151.0, 12.0, 0.0),
        longitude_ref="W",
    )

    metadata = service.extract(content)

    assert metadata["latitude"] == pytest.approx(-33.8666667)
    assert metadata["longitude"] == pytest.approx(-151.2)


def test_extract_complete_metadata(service):
    """
    Verify extraction of capture time, GPS, and camera
    metadata together.
    """

    content = create_test_image(
        captured_at="2026:08:13 10:15:30",
        latitude=(28.0, 36.0, 0.0),
        latitude_ref="N",
        longitude=(77.0, 12.0, 0.0),
        longitude_ref="E",
        make="Nikon",
        model="Z8",
    )

    metadata = service.extract(content)

    assert metadata["captured_at"] == datetime(
        2026,
        8,
        13,
        10,
        15,
        30,
        tzinfo=timezone.utc,
    )

    assert metadata["latitude"] == pytest.approx(28.6)
    assert metadata["longitude"] == pytest.approx(77.2)

    assert metadata["camera_make"] == "Nikon"
    assert metadata["camera_model"] == "Z8"
    assert metadata["metadata_source"] == "exif"


def test_extract_invalid_image_returns_empty_metadata(
    service,
):
    """
    Verify that invalid image bytes do not cause metadata
    extraction to fail.
    """

    metadata = service.extract(
        b"this is not an image"
    )

    assert metadata == {}


def test_extract_invalid_capture_time_is_ignored(
    service,
):
    """
    Verify that malformed capture timestamps are ignored
    without breaking metadata extraction.
    """

    content = create_test_image(
        captured_at="invalid-date",
        make="Canon",
    )

    metadata = service.extract(content)

    assert "captured_at" not in metadata
    assert metadata["camera_make"] == "Canon"
    assert metadata["metadata_source"] == "exif"


def test_extract_partial_gps_metadata(
    service,
):
    """
    Verify that incomplete GPS information does not produce
    invalid coordinates.
    """

    content = create_test_image(
        latitude=(28.0, 36.0, 0.0),
        latitude_ref="N",
    )

    metadata = service.extract(content)

    assert metadata["latitude"] == pytest.approx(28.6)
    assert "longitude" not in metadata
    assert metadata["metadata_source"] == "exif"