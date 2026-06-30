#!/usr/bin/env python3
"""Fetch YouTube metadata candidates for BibleMaxxing.

This script uses official YouTube Data API endpoints and prints JSON candidates
that can be posted to `/biblemaxxing/api/v1/admin/ingest/candidates`.
It does not download, cache, or store audiovisual content.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.youtube import fetch_candidates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="Christian Bible Jesus Shorts")
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--api-key", default=os.getenv("BIBLEMAXXING_YOUTUBE_API_KEY"))
    args = parser.parse_args()

    if not args.api_key:
        print("Missing --api-key or BIBLEMAXXING_YOUTUBE_API_KEY", file=sys.stderr)
        return 2

    candidates = [
        candidate.model_dump(mode="json")
        for candidate in fetch_candidates(args.api_key, args.query, args.max_results)
    ]
    print(json.dumps({"candidates": candidates}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
