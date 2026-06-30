from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from app.schemas import YouTubeCandidate

API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def request_json(path: str, params: dict[str, str | int]) -> dict[str, Any]:
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise YouTubeAPIError(
            f"YouTube API {path} failed with {exc.code}: {body[:400]}",
            status_code=exc.code,
            body=body,
        ) from exc
    except urllib.error.URLError as exc:
        raise YouTubeAPIError(f"YouTube API {path} request failed: {exc.reason}") from exc


def parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return None
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_candidates(api_key: str, query: str, max_results: int) -> list[YouTubeCandidate]:
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
    candidates: list[YouTubeCandidate] = []
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
            YouTubeCandidate(
                youtube_video_id=item["id"],
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                thumbnail_url=thumbnail.get("url"),
                published_at=parse_datetime(snippet.get("publishedAt")),
                duration_seconds=parse_duration(item.get("contentDetails", {}).get("duration")),
                tags=snippet.get("tags", []),
            )
        )
    return candidates
