import pytest

from postbode.credentials import (
    CredentialError,
    YouTubeCredential,
    load_youtube_credential,
)


def test_missing_credentials_fail_closed():
    with pytest.raises(CredentialError):
        load_youtube_credential({})


def test_fingerprint_does_not_expose_secret():
    credential = YouTubeCredential("client-value", "secret-value", "refresh-value")
    assert credential.fingerprint() != credential.client_id
    assert "secret-value" not in credential.fingerprint()
