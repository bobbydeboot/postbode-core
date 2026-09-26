# Postbode Core

Postbode Core is a small Python toolkit for fail-closed media publishing with
exact artifact binding, idempotent delivery, credential isolation,
private-first workflows, provider readback, and durable secret-safe receipts.

## Why Postbode Core

Media APIs are easy to call but harder to call safely and repeatably. This
project provides contracts and provider boundaries that make the intended
artifact, destination, authority, and remote result explicit.

## Reliability guarantees

- Requests validate the artifact's exact SHA-256 before a provider call.
- Destination identity and authenticated channel identity are checked.
- Idempotency keys prevent conflicting intent and ambiguous retries.
- Private-first operation is the safe default; non-private requests need an
  exact authority record.
- Provider readback is checked against the plan before completion.
- Receipts store identifiers and digests, never raw credentials.

These are library-level checks. Applications remain responsible for their
provider transport, credential storage, authorization, and operational policy.

## Installation

```console
pip install -e ".[test]"
```

## Quick start

The following creates a local plan and performs no provider mutation:

```python
from pathlib import Path
import hashlib

from postbode import DestinationPolicy, PublicationRequest, build_plan

artifact = Path("examples/fake-media.mp4")
request = PublicationRequest(
    destination_id="example-destination",
    platform="youtube",
    artifact_path=artifact,
    artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
    title="Example upload",
    description="A local dry-run example.",
    privacy_status="private",
    idempotency_key="example-content-001",
    explicit_authority=True,
)
policy = DestinationPolicy("example-destination", "youtube", "UC_EXAMPLE_CHANNEL_ID")
plan = build_plan(request, policy)
print(plan.request_identity)
```

## Safety model

Provider mutations require an application-supplied authenticated transport and
explicit authority where applicable. The YouTube transport can build and send
a private multipart upload, but applications still own token acquisition and
authorization. The package does not silently retry an ambiguous submission or
treat a plan as proof of remote state; it performs provider readback after a
write. Use a fake transport in tests.

## Supported capabilities

The public core currently provides validated YouTube request contracts,
destination policies, deterministic plans, safe credential fingerprints,
secret-free receipts, injectable YouTube channel/video readback transport,
private multipart upload support, generic asset descriptor validation, and
generic channel-branding data validation.

## Non-goals

Postbode Core does not generate media, choose content, optimize audiences, make
creative decisions, or contain a content recommendation engine.

## Development

```console
pytest
ruff check .
black --check .
python -m compileall -q postbode
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
