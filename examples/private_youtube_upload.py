"""Illustrative private-first setup; this file performs no network call."""

from pathlib import Path

from postbode import DestinationPolicy, PublicationRequest, build_plan


def make_plan() -> object:
    artifact = Path("examples/fake-media.mp4")
    import hashlib

    request = PublicationRequest(
        "example-destination",
        "youtube",
        artifact,
        hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "Example private upload",
        "Fictitious local example.",
        "private",
        "example-content-001",
        True,
    )
    return build_plan(
        request,
        DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"),
    )


if __name__ == "__main__":
    print(make_plan().request_identity)
