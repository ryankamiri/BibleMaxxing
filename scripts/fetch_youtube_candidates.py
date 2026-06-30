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
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime


API_BASE = "https://www.googleapis.com/youtube/v3"


def request_json(path: str, params: dict[str, str | int]) -> dict:
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return None
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def parse_datetime(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def fetch_candidates(api_key: str, query: str, max_results: int) -> list[dict]:
    search = request_json(
        "search",
        {
            "key": api_key,
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoDuration": "short",
            "videoEmbeddable": "true",
            "safeSearch": "strict",
            "order": "relevance",
            "maxResults": min(max_results, 50),
        },
    )
    video_ids = [
        item["id"]["videoId"]
        for item in search.get("items", [])
        if item.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return []

    videos = request_json(
        "videos",
        {
            "key": api_key,
            "part": "snippet,contentDetails,status",
            "id": ",".join(video_ids),
            "maxResults": len(video_ids),
        },
    )
    candidates = []
    for item in videos.get("items", []):
        status = item.get("status", {})
        if status.get("embeddable") is False or status.get("privacyStatus") != "public":
            continue
        snippet = item.get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("maxres")
            or thumbnails.get("standard")
            or thumbnails.get("high")
            or thumbnails.get("medium")
            or thumbnails.get("default")
            or {}
        )
        candidates.append(
            {
                "youtube_video_id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "thumbnail_url": thumbnail.get("url"),
                "published_at": parse_datetime(snippet.get("publishedAt")),
                "duration_seconds": parse_duration(
                    item.get("contentDetails", {}).get("duration")
                ),
                "tags": snippet.get("tags", []),
            }
        )
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="Christian Bible Jesus Shorts")
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--api-key", default=os.getenv("BIBLEMAXXING_YOUTUBE_API_KEY"))
    args = parser.parse_args()

    if not args.api_key:
        print("Missing --api-key or BIBLEMAXXING_YOUTUBE_API_KEY", file=sys.stderr)
        return 2

    print(json.dumps({"candidates": fetch_candidates(args.api_key, args.query, args.max_results)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

