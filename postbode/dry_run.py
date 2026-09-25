from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import PublicationRequest
from .destination import DestinationPolicy
from .plan import build_plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a secret-free YouTube publication plan"
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--destination", default="example-destination")
    parser.add_argument("--channel-id", default="UC_EXAMPLE_CHANNEL_ID")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument(
        "--privacy", choices=("private", "unlisted", "public"), default="private"
    )
    args = parser.parse_args()
    request = PublicationRequest(
        args.destination,
        "youtube",
        args.artifact,
        args.sha256,
        args.title,
        args.description,
        args.privacy,
        args.idempotency_key,
        True,
        made_for_kids=False,
    )
    policy = DestinationPolicy(args.destination, "youtube", args.channel_id)
    print(json.dumps(build_plan(request, policy).as_dict(), indent=2, sort_keys=True))
    print("provider_mutations=0")


if __name__ == "__main__":
    main()
