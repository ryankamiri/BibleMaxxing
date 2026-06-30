#!/usr/bin/env python3
"""Verify feed append behavior against a local or deployed BibleMaxxing API."""

from __future__ import annotations

import argparse
import json
import secrets
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def normalize_service_base(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/biblemaxxing"):
        return normalized
    return f"{normalized}/biblemaxxing"


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read()
            return json.loads(body.decode() or "{}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"{method} {url} failed with {error.code}: {detail}") from error


def feed_video_ids(feed: dict[str, Any]) -> list[str]:
    video_ids: list[str] = []
    for item in feed.get("items", []):
        video = item.get("video")
        if item.get("type") == "video" and video and video.get("id"):
            video_ids.append(video["id"])
    return video_ids


def random_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(24))


def fetch_feed(
    api_base: str,
    token: str,
    limit: int,
    excluded_video_ids: list[str] | None = None,
) -> dict[str, Any]:
    params: list[tuple[str, str]] = [("limit", str(limit))]
    for video_id in excluded_video_ids or []:
        params.append(("exclude_video_ids", video_id))
    query = urllib.parse.urlencode(params)
    return request_json("GET", f"{api_base}/feed?{query}", token=token)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a throwaway user and verify /feed append pages do not repeat loaded videos."
    )
    parser.add_argument(
        "--base-url",
        default="https://api.tailortom.org/biblemaxxing",
        help="Service base URL, with or without /biblemaxxing.",
    )
    parser.add_argument("--first-limit", type=int, default=5)
    parser.add_argument("--second-limit", type=int, default=8)
    parser.add_argument("--email-prefix", default="scrollcheck")
    parser.add_argument("--keep-user", action="store_true", help="Do not delete the throwaway user.")
    args = parser.parse_args()

    service_base = normalize_service_base(args.base_url)
    api_base = f"{service_base}/api/v1"
    run_id = f"{int(time.time())}-{secrets.token_hex(3)}"
    email = f"{args.email_prefix}+{run_id}@example.com"
    username = f"{args.email_prefix}{run_id.replace('-', '')}"[:40]
    password = random_password()
    token: str | None = None

    try:
        request_json("GET", f"{service_base}/health")
        auth = request_json(
            "POST",
            f"{api_base}/auth/register",
            {
                "username": username,
                "email": email,
                "password": password,
                "birthday": "2005-01-01",
            },
        )
        token = auth["access_token"]
        request_json(
            "POST",
            f"{api_base}/onboarding",
            {"topicSlugs": ["Prayer", "Bible study", "Workplace holiness"], "intensity": "balanced"},
            token=token,
        )

        page_one = fetch_feed(api_base, token, args.first_limit)
        page_one_ids = feed_video_ids(page_one)
        if not page_one_ids:
            raise RuntimeError("First feed page returned no video items.")

        page_two = fetch_feed(api_base, token, args.second_limit, page_one_ids)
        page_two_ids = feed_video_ids(page_two)
        if not page_two_ids:
            raise RuntimeError("Second feed page returned no video items.")

        duplicates = sorted(set(page_one_ids).intersection(page_two_ids))
        if duplicates:
            raise RuntimeError(f"Second feed page repeated loaded videos: {duplicates}")

        summary = {
            "service_base": service_base,
            "page_one_video_count": len(page_one_ids),
            "page_two_video_count": len(page_two_ids),
            "duplicates": duplicates,
            "excluded_count": len(page_one_ids),
            "page_two_sample": page_two_ids[:5],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    finally:
        if token and not args.keep_user:
            try:
                request_json("DELETE", f"{api_base}/me", token=token)
            except Exception as error:  # noqa: BLE001
                print(f"warning: failed to delete throwaway user {email}: {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
