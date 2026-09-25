import pytest

from postbode.asset_ingress import AssetDescriptor, validate_asset
from postbode.contracts import PublicationError


def test_drive_like_asset_validation_rejects_wrong_metadata():
    value = AssetDescriptor("asset-001", "example.mp4", "video/mp4", 10, "a" * 64)
    with pytest.raises(PublicationError, match="filename"):
        validate_asset(
            value,
            expected_id="asset-001",
            expected_filename="other.mp4",
            expected_mime="video/mp4",
            expected_sha256="a" * 64,
        )
