import hashlib
from pathlib import Path

from postbode import DestinationPolicy, PublicationRequest, build_plan

artifact = Path(__file__).with_name("fake-media.mp4")
request = PublicationRequest(
    "example-destination",
    "youtube",
    artifact,
    hashlib.sha256(artifact.read_bytes()).hexdigest(),
    "Mock dry run",
    "No provider mutation occurs.",
    "private",
    "example-content-001",
    True,
)
plan = build_plan(
    request,
    DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID"),
)
print({"request_identity": plan.request_identity, "provider_mutations": 0})
