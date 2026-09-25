"""Fail-closed publication tree scanner used by the local audit."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORBIDDEN_TERMS = (
    "output" + " atlas",
    "output" + "_atlas",
    "had" + "rian",
    "mining" + " trucks",
    "captain" + " bobby",
    "captain" + "bobby",
    "bobby" + " de boot",
    "nora" + " kade",
    "nora" + "_kade",
    "buy" + "cue",
    "mart" + "industries",
    "studio" + " atlas",
    "captain" + "bobbystudio",
    "bobbytheboat" + ".com",
    "owner" + "-review",
)
SECRET_PATTERNS = (
    re.compile(r"(?i)(client_secret|refresh_token|access_token)\s*[=:]\s*['\"][^'\"]+"),
    re.compile(r"UC[A-Za-z0-9_-]{20,}"),
    re.compile(r"[0-9a-f]{64}"),
)
GENERIC_VALUES = {"UC_EXAMPLE_CHANNEL_ID"}


def scan(root: Path) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    ignored_dirs = {
        ".git",
        ".pytest-temp",
        ".pytest_cache",
        "__pycache__",
        "build",
        "dist",
        "postbode_core.egg-info",
    }
    for path in sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and not ignored_dirs.intersection(p.parts)
    ):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.casefold()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "kind": "forbidden_term",
                        "value": term,
                    }
                )
        for pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match and match.group(0) not in GENERIC_VALUES:
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "kind": "suspicious_pattern",
                        "value": pattern.pattern,
                    }
                )
    return {
        "pass": not findings,
        "findings": findings,
        "files_scanned": sum(
            1
            for p in root.rglob("*")
            if p.is_file() and not ignored_dirs.intersection(p.parts)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan(args.root)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
