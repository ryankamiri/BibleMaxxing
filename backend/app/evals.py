from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, services
from app.config import Settings
from app.schemas import YouTubeCandidate


@dataclass
class EvalScorecard:
    name: str
    overall_score: float
    status: str
    metrics: dict[str, float | int | str] = field(default_factory=dict)
    gates: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "overall_score": round(self.overall_score, 2),
            "status": self.status,
            "metrics": self.metrics,
            "gates": self.gates,
            "notes": self.notes,
            "generated_at": self.generated_at,
        }


def _mean(values: list[float], fallback: float = 0) -> float:
    return round(mean(values), 4) if values else fallback


def _safe_share(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0


def _score_status(score: float, gates: dict[str, bool]) -> str:
    if not all(gates.values()):
        return "regressed"
    if score >= 80:
        return "healthy"
    if score >= 65:
        return "baseline"
    return "watch"


def compare_scorecards(
    current: EvalScorecard | dict[str, Any],
    baseline: EvalScorecard | dict[str, Any] | None,
    min_delta: float = 2.5,
) -> dict[str, Any]:
    current_data = current.to_dict() if isinstance(current, EvalScorecard) else current
    if baseline is None:
        return {
            "name": current_data["name"],
            "status": "no_baseline",
            "delta": None,
            "current_score": current_data["overall_score"],
            "baseline_score": None,
        }

    baseline_data = baseline.to_dict() if isinstance(baseline, EvalScorecard) else baseline
    delta = round(float(current_data["overall_score"]) - float(baseline_data["overall_score"]), 2)
    if delta >= min_delta:
        status = "improving"
    elif delta <= -min_delta:
        status = "regressing"
    else:
        status = "baselining"

    return {
        "name": current_data["name"],
        "status": status,
        "delta": delta,
        "current_score": current_data["overall_score"],
        "baseline_score": baseline_data["overall_score"],
    }


def evaluate_recommendation_feed(
    videos: list[models.Video],
    limit: int,
    name: str = "recommendation_feed",
) -> EvalScorecard:
    total = len(videos)
    creator_counts = Counter(video.creator_id for video in videos)
    source_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    for video in videos:
        source_counts.update(services.source_diversity_keys(video))
        topic_counts.update(services.video_topic_set(video))

    consecutive_creator_repeats = sum(
        left.creator_id == right.creator_id for left, right in zip(videos, videos[1:], strict=False)
    )
    consecutive_source_repeats = sum(
        bool(
            services.source_diversity_keys(left).intersection(
                services.source_diversity_keys(right)
            )
        )
        for left, right in zip(videos, videos[1:], strict=False)
    )
    fit_scores = [
        services.reel_fit_score(video.duration_seconds, video.title, video.description, video.tags)
        for video in videos
    ]
    spiritual_scores = [video.spiritual_score for video in videos]
    theology_scores = [video.theology_score for video in videos]
    trusted_count = sum(
        services.TRUSTED_INFLUENCER_TOPIC in (video.topics or [])
        or bool(
            isinstance(video.creator.theology_profile if video.creator else None, dict)
            and video.creator.theology_profile.get("trusted_influencer")
        )
        for video in videos
    )

    max_creator_share = _safe_share(max(creator_counts.values(), default=0), total)
    max_source_share = _safe_share(max(source_counts.values(), default=0), total)
    feed_fill = min(1.0, total / max(limit, 1))
    creator_coverage = _safe_share(len(creator_counts), total)
    topic_coverage = _safe_share(len(topic_counts), max(total, 1))
    no_creator_repeat_score = 1 - _safe_share(consecutive_creator_repeats, max(total - 1, 1))
    no_source_repeat_score = 1 - _safe_share(consecutive_source_repeats, max(total - 1, 1))

    avg_spiritual = _mean(spiritual_scores)
    avg_theology = _mean(theology_scores)
    avg_fit = _mean(fit_scores)
    score = (
        avg_spiritual * 24
        + avg_theology * 24
        + avg_fit * 10
        + feed_fill * 8
        + creator_coverage * 12
        + min(topic_coverage, 1) * 8
        + (1 - min(max_creator_share, 1)) * 6
        + (1 - min(max_source_share, 1)) * 4
        + no_creator_repeat_score * 2
        + no_source_repeat_score * 2
    )
    gates = {
        "has_feed_inventory": total >= min(limit, 5),
        "theology_floor": min(theology_scores, default=0) >= 0.5,
        "creator_not_dominant": max_creator_share <= 0.35 or total <= 3,
        "source_not_dominant": max_source_share <= 0.35 or total <= 3,
        "no_back_to_back_source_repeat": consecutive_source_repeats == 0,
    }
    notes: list[str] = []
    if max_source_share > 0.35:
        notes.append("One aligned preacher/source topic is dominating the feed.")
    if consecutive_source_repeats:
        notes.append("Back-to-back aligned source repeats found.")
    if avg_theology < 0.65:
        notes.append("Average theology score is below the preferred floor.")

    return EvalScorecard(
        name=name,
        overall_score=score,
        status=_score_status(score, gates),
        metrics={
            "feed_count": total,
            "requested_limit": limit,
            "avg_spiritual_score": avg_spiritual,
            "avg_theology_score": avg_theology,
            "avg_reel_fit_score": avg_fit,
            "creator_coverage": creator_coverage,
            "topic_coverage": topic_coverage,
            "max_creator_share": max_creator_share,
            "max_source_share": max_source_share,
            "trusted_influencer_share": _safe_share(trusted_count, total),
            "consecutive_creator_repeats": consecutive_creator_repeats,
            "consecutive_source_repeats": consecutive_source_repeats,
        },
        gates=gates,
        notes=notes,
    )


def evaluate_recommendations_for_user(
    db: Session,
    user: models.User,
    limit: int = 30,
) -> EvalScorecard:
    videos = services.feed_for_user(db, user, limit)
    return evaluate_recommendation_feed(
        videos,
        limit=limit,
        name=f"recommendation_feed:{user.email}",
    )


def existing_youtube_ids_for_candidates(
    db: Session, candidates: list[YouTubeCandidate]
) -> set[str]:
    candidate_ids = [candidate.youtube_video_id for candidate in candidates]
    if not candidate_ids:
        return set()
    return set(
        db.scalars(
            select(models.Video.youtube_video_id).where(models.Video.youtube_video_id.in_(candidate_ids))
        )
    )


def candidate_contains_excluded_keyword(candidate: YouTubeCandidate) -> bool:
    text = (
        f"{candidate.title} {candidate.description} {candidate.channel_title} "
        f"{' '.join(candidate.tags)}"
    ).lower()
    return any(keyword in text for keyword in services.EXCLUDED_KEYWORDS)


def evaluate_ingest_candidates(
    candidates: list[YouTubeCandidate],
    query: str | None = None,
    existing_youtube_ids: set[str] | None = None,
    name: str = "youtube_ingest_candidates",
) -> EvalScorecard:
    existing_youtube_ids = existing_youtube_ids or set()
    total = len(candidates)
    accepted = 0
    rejected = 0
    duplicates = 0
    trusted = 0
    red_flag_candidates = 0
    red_flag_auto_approved = 0
    spiritual_scores: list[float] = []
    theology_scores: list[float] = []
    fit_scores: list[float] = []
    channel_ids: set[str] = set()

    for candidate in candidates:
        channel_ids.add(candidate.channel_id)
        is_duplicate = candidate.youtube_video_id in existing_youtube_ids
        if is_duplicate:
            duplicates += 1

        approved, topics, spiritual_score, theology_score = services.classify_candidate(candidate)
        has_red_flag = candidate_contains_excluded_keyword(candidate)
        if has_red_flag:
            red_flag_candidates += 1
        if approved and has_red_flag:
            red_flag_auto_approved += 1
        if services.TRUSTED_INFLUENCER_TOPIC in topics:
            trusted += 1

        if approved and not is_duplicate:
            accepted += 1
            spiritual_scores.append(spiritual_score)
            theology_scores.append(theology_score)
            fit_scores.append(
                services.reel_fit_score(
                    candidate.duration_seconds,
                    candidate.title,
                    candidate.description,
                    candidate.tags,
                )
            )
        elif not approved:
            rejected += 1

    non_duplicate_total = max(total - duplicates, 0)
    avg_spiritual = _mean(spiritual_scores)
    avg_theology = _mean(theology_scores)
    avg_fit = _mean(fit_scores)
    duplicate_share = _safe_share(duplicates, total)
    useful_new_rate = _safe_share(accepted, max(non_duplicate_total, 1))
    channel_coverage = _safe_share(len(channel_ids), total)
    score = (
        avg_spiritual * 25
        + avg_theology * 25
        + avg_fit * 12
        + useful_new_rate * 15
        + channel_coverage * 8
        + (1 - duplicate_share) * 10
        + _safe_share(trusted, max(total, 1)) * 5
    )
    if red_flag_auto_approved:
        score = max(0, score - 40)

    gates = {
        "has_candidates": total > 0,
        "no_red_flag_auto_approved": red_flag_auto_approved == 0,
        "some_new_approved_candidates": accepted > 0 or total == 0,
        "duplicate_waste_under_half": duplicate_share <= 0.5,
    }
    notes: list[str] = []
    if red_flag_auto_approved:
        notes.append("Excluded/heretical keywords were auto-approved by classification.")
    if duplicate_share > 0.5:
        notes.append("More than half the candidate batch already exists.")
    if accepted == 0 and total:
        notes.append("No new approved candidates found in this batch.")

    metrics: dict[str, float | int | str] = {
        "candidate_count": total,
        "accepted_new_count": accepted,
        "rejected_by_filter_count": rejected,
        "duplicate_count": duplicates,
        "trusted_influencer_candidate_count": trusted,
        "red_flag_candidate_count": red_flag_candidates,
        "red_flag_auto_approved_count": red_flag_auto_approved,
        "unique_channel_count": len(channel_ids),
        "useful_new_rate": useful_new_rate,
        "duplicate_share": duplicate_share,
        "avg_spiritual_score": avg_spiritual,
        "avg_theology_score": avg_theology,
        "avg_reel_fit_score": avg_fit,
    }
    if query:
        metrics["query"] = query

    return EvalScorecard(
        name=name if not query else f"{name}:{query}",
        overall_score=score,
        status=_score_status(score, gates),
        metrics=metrics,
        gates=gates,
        notes=notes,
    )


def evaluate_query_plan(settings: Settings, queries: list[str]) -> EvalScorecard:
    broad_queries = set(settings.youtube_ingest_query_list)
    pastor_queries = set(settings.youtube_ingest_pastor_query_list)
    query_set = set(queries)
    broad_count = len(query_set.intersection(broad_queries))
    pastor_count = len(query_set.intersection(pastor_queries))
    duplicate_count = len(queries) - len(query_set)
    score = (
        min(broad_count / max(len(broad_queries), 1), 1) * 45
        + min(pastor_count / max(settings.youtube_ingest_pastor_queries_per_cycle, 1), 1) * 35
        + (1 - _safe_share(duplicate_count, max(len(queries), 1))) * 20
    )
    gates = {
        "has_broad_discovery_lane": broad_count > 0,
        "has_pastor_source_lane": pastor_count > 0,
        "no_duplicate_queries": duplicate_count == 0,
    }
    return EvalScorecard(
        name="youtube_ingest_query_plan",
        overall_score=score,
        status=_score_status(score, gates),
        metrics={
            "query_count": len(queries),
            "broad_query_count": broad_count,
            "pastor_query_count": pastor_count,
            "duplicate_query_count": duplicate_count,
        },
        gates=gates,
    )


def red_team_youtube_candidates() -> list[YouTubeCandidate]:
    return [
        YouTubeCandidate(
            youtube_video_id="red-mormon",
            title="Jesus and the restored gospel from Mormon teaching",
            description="LDS doctrine presented as Christian Bible truth.",
            channel_id="red-1",
            channel_title="Mormon Bible Clips",
            duration_seconds=58,
            tags=["Jesus", "Bible", "LDS"],
        ),
        YouTubeCandidate(
            youtube_video_id="red-jw",
            title="Jehovah Witness answer about Jesus",
            description="Watchtower teaching with Bible verses.",
            channel_id="red-2",
            channel_title="Watchtower Shorts",
            duration_seconds=61,
            tags=["Bible", "Jesus"],
        ),
        YouTubeCandidate(
            youtube_video_id="red-oneness",
            title="Oneness Pentecostal sermon about Jesus name baptism",
            description="Oneness doctrine framed as gospel truth.",
            channel_id="red-3",
            channel_title="Oneness Clips",
            duration_seconds=55,
            tags=["Jesus", "sermon"],
        ),
        YouTubeCandidate(
            youtube_video_id="red-sda",
            title="Seventh-day Adventist prophecy chart for the end times",
            description="Bible prophecy and Sabbath doctrine.",
            channel_id="red-4",
            channel_title="SDA Prophecy Shorts",
            duration_seconds=59,
            tags=["Bible", "prophecy"],
        ),
        YouTubeCandidate(
            youtube_video_id="red-prosperity",
            title="Prosperity gospel prayer to manifest money today",
            description="Use faith and manifestation to unlock wealth.",
            channel_id="red-5",
            channel_title="Manifest Your Blessing",
            duration_seconds=45,
            tags=["prayer", "God"],
        ),
        YouTubeCandidate(
            youtube_video_id="good-workplace",
            title="Being faithful to Christ at work",
            description="Bible encouragement for workplace holiness and discipleship.",
            channel_id="good-1",
            channel_title="Christian Career Tools",
            duration_seconds=59,
            tags=["Bible", "Jesus", "discipleship", "workplace"],
        ),
    ]


def evaluate_red_team_ingestion() -> EvalScorecard:
    return evaluate_ingest_candidates(
        red_team_youtube_candidates(),
        query="red-team-fixtures",
        existing_youtube_ids=set(),
        name="youtube_ingest_red_team",
    )
