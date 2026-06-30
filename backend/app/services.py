from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import ceil

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app import models
from app.schemas import ReflectionCard, YouTubeCandidate

CHRISTIAN_KEYWORDS = {
    "acts",
    "bible",
    "jesus",
    "christ",
    "gospel",
    "scripture",
    "prayer",
    "christian",
    "god",
    "grace",
    "holy spirit",
    "lord",
    "sermon",
    "worship",
    "discipleship",
    "faith",
    "pastor",
    "preach",
    "preaching",
    "proverbs",
    "psalm",
    "repent",
    "repentance",
    "romans",
    "salvation",
    "sin",
    "church",
    "cross",
    "john",
}

ALIGNED_SOURCE_TOPICS = {
    "2819 church": "philip-anthony-mitchell",
    "philip anthony mitchell": "philip-anthony-mitchell",
    "bryce crawford": "bryce-crawford",
    "bryce crawford podcast": "bryce-crawford",
    "cliffe knechtle": "cliffe-knechtle",
    "stuart knechtle": "cliffe-knechtle",
    "give me an answer": "cliffe-knechtle",
    "askcliffe": "cliffe-knechtle",
    "bibleproject": "bibleproject",
    "tim mackie": "tim-mackie",
    "gavin ortlund": "gavin-ortlund",
    "truth unites": "gavin-ortlund",
    "john piper": "john-piper",
    "desiring god": "john-piper",
    "tim keller": "tim-keller",
    "gospel in life": "tim-keller",
    "david platt": "david-platt",
    "matt chandler": "matt-chandler",
    "the village church": "matt-chandler",
}

TRUSTED_INFLUENCER_TOPIC = "trusted-influencer"
PASTOR_CLIPS_TOPIC = "pastor-clips"
TRUSTED_INFLUENCER_BOOST = 0.22
TOPIC_WEIGHT_MIN = -0.35
TOPIC_WEIGHT_MAX = 0.42
CREATOR_WEIGHT_MIN = -0.24
CREATOR_WEIGHT_MAX = 0.28
RANK_TOPIC_SIGNAL_MIN = -0.22
RANK_TOPIC_SIGNAL_MAX = 0.28
RANK_CREATOR_SIGNAL_MIN = -0.14
RANK_CREATOR_SIGNAL_MAX = 0.18
CREATOR_REPEAT_PENALTY = 0.16
TOPIC_REPEAT_PENALTY = 0.025
NEW_CREATOR_BONUS = 0.08
NEW_TOPIC_BONUS = 0.04
MAX_CREATOR_SHARE = 0.25

EXCLUDED_KEYWORDS = {
    "mormon",
    "lds",
    "jehovah",
    "watchtower",
    "oneness",
    "prosperity gospel",
    "manifestation",
    "law of attraction",
    "rapture chart",
}


@dataclass
class UserInterestProfile:
    topic_weights: dict[str, float] = field(default_factory=dict)
    creator_weights: dict[str, float] = field(default_factory=dict)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def reel_fit_score(
    duration_seconds: int | None,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
) -> float:
    """Prefer Shorts-like videos without banning useful landscape content."""
    if duration_seconds is None:
        duration_score = 0.56
    elif duration_seconds <= 75:
        duration_score = 1.0
    elif duration_seconds <= 120:
        duration_score = 0.82
    elif duration_seconds <= 180:
        duration_score = 0.64
    elif duration_seconds <= 300:
        duration_score = 0.38
    else:
        duration_score = 0.18

    tag_values = tags or []
    text = f"{title} {description} {' '.join(tag_values)}".lower()
    shorts_hint = any(
        marker in text
        for marker in ("#shorts", " shorts", "shorts ", "short-form", "short video")
    )
    hint_score = 1.0 if shorts_hint else 0.68
    return round(duration_score * 0.78 + hint_score * 0.22, 3)


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part)


def normalize_topic(value: str) -> str:
    return slugify(value)


def video_topic_set(video: models.Video) -> set[str]:
    return {topic for topic in (normalize_topic(value) for value in video.topics or []) if topic}


def bump_weight(
    weights: dict[str, float],
    key: str | None,
    delta: float,
    lower: float,
    upper: float,
) -> None:
    if not key:
        return
    weights[key] = clamp(weights.get(key, 0) + delta, lower, upper)


def apply_video_feedback(
    profile: UserInterestProfile,
    video: models.Video,
    topic_delta: float,
    creator_delta: float,
) -> None:
    for topic in video_topic_set(video):
        bump_weight(profile.topic_weights, topic, topic_delta, TOPIC_WEIGHT_MIN, TOPIC_WEIGHT_MAX)
    bump_weight(
        profile.creator_weights,
        video.creator_id,
        creator_delta,
        CREATOR_WEIGHT_MIN,
        CREATOR_WEIGHT_MAX,
    )


def classify_candidate(candidate: YouTubeCandidate) -> tuple[bool, list[str], float, float]:
    text = (
        f"{candidate.title} {candidate.description} {candidate.channel_title} "
        f"{' '.join(candidate.tags)}"
    ).lower()
    matched = sorted(keyword for keyword in CHRISTIAN_KEYWORDS if keyword in text)
    source_matches = sorted(keyword for keyword in ALIGNED_SOURCE_TOPICS if keyword in text)
    excluded = any(keyword in text for keyword in EXCLUDED_KEYWORDS)
    spiritual_score = min(1.0, 0.35 + len(matched) * 0.08 + len(source_matches) * 0.06)
    theology_score = (
        0.2
        if excluded
        else min(1.0, 0.55 + len(matched) * 0.04 + len(source_matches) * 0.03)
    )

    topics = matched[:8]
    if source_matches:
        source_topics = sorted({ALIGNED_SOURCE_TOPICS[source] for source in source_matches})
        topics = unique_preserving_order(
            [TRUSTED_INFLUENCER_TOPIC, PASTOR_CLIPS_TOPIC, *source_topics, *topics]
        )

    return (
        (bool(matched) or bool(source_matches)) and not excluded,
        topics,
        spiritual_score,
        theology_score,
    )


def upsert_youtube_candidates(
    db: Session, candidates: list[YouTubeCandidate], default_approve: bool = True
) -> tuple[int, int]:
    created = 0
    skipped = 0
    for candidate in candidates:
        exists = db.scalar(
            select(models.Video).where(models.Video.youtube_video_id == candidate.youtube_video_id)
        )
        if exists:
            skipped += 1
            continue

        approved_by_filter, topics, spiritual_score, theology_score = classify_candidate(candidate)
        if not approved_by_filter:
            skipped += 1
            continue

        creator = db.scalar(
            select(models.Creator).where(models.Creator.youtube_channel_id == candidate.channel_id)
        )
        if creator is None:
            creator = models.Creator(
                handle=f"@{slugify(candidate.channel_title) or candidate.channel_id}",
                display_name=candidate.channel_title,
                youtube_channel_id=candidate.channel_id,
            )
            db.add(creator)
            db.flush()

        moderation_status = "approved" if default_approve else "pending"
        if TRUSTED_INFLUENCER_TOPIC in topics:
            creator_profile = creator.theology_profile or {}
            influencer_slugs = sorted(
                set(creator_profile.get("trusted_influencer_slugs", []))
                .union(set(topics).intersection(set(ALIGNED_SOURCE_TOPICS.values())))
            )
            creator.theology_profile = {
                **creator_profile,
                "trusted_influencer": True,
                "trusted_influencer_slugs": influencer_slugs,
            }

        fit_score = reel_fit_score(
            candidate.duration_seconds, candidate.title, candidate.description, candidate.tags
        )
        video = models.Video(
            creator_id=creator.id,
            youtube_video_id=candidate.youtube_video_id,
            title=candidate.title,
            description=candidate.description,
            thumbnail_url=candidate.thumbnail_url,
            duration_seconds=candidate.duration_seconds,
            source_url=f"https://www.youtube.com/shorts/{candidate.youtube_video_id}",
            embed_url=f"https://www.youtube.com/embed/{candidate.youtube_video_id}?playsinline=1&enablejsapi=1",
            published_at=candidate.published_at,
            tags=candidate.tags,
            topics=topics,
            moderation_status=moderation_status,
            spiritual_score=spiritual_score,
            theology_score=theology_score,
            entertainment_score=0.45 + fit_score * 0.3,
            freshness_score=0.7,
        )
        db.add(video)
        created += 1
    db.commit()
    return created, skipped


def seed_sample_inventory(db: Session) -> tuple[int, int]:
    samples = [
        YouTubeCandidate(
            youtube_video_id="p7XRPGzL6kk",
            title="Who is Jesus?",
            description=(
                "BibleProject short on the identity of Jesus, Christ-centered discipleship, "
                "and Scripture."
            ),
            channel_id="UCVfwlh9XpX2Y_tQfjeln9QA",
            channel_title="BibleProject",
            thumbnail_url="https://i.ytimg.com/vi/p7XRPGzL6kk/hqdefault.jpg",
            duration_seconds=59,
            tags=["Bible", "Jesus", "Christian", "Scripture"],
        ),
        YouTubeCandidate(
            youtube_video_id="YMOB4hWKqfw",
            title="Jesus Feeds People in the Wilderness",
            description="BibleProject short about Jesus, the wilderness, and gospel provision.",
            channel_id="UCVfwlh9XpX2Y_tQfjeln9QA",
            channel_title="BibleProject",
            thumbnail_url="https://i.ytimg.com/vi/YMOB4hWKqfw/hqdefault.jpg",
            duration_seconds=59,
            tags=["Bible", "Jesus", "gospel", "discipleship"],
        ),
        YouTubeCandidate(
            youtube_video_id="jGKFWfpAfZY",
            title="Do not worry.",
            description="BibleProject short connecting Jesus, anxiety, prayer, and Scripture.",
            channel_id="UCVfwlh9XpX2Y_tQfjeln9QA",
            channel_title="BibleProject",
            thumbnail_url="https://i.ytimg.com/vi/jGKFWfpAfZY/hqdefault.jpg",
            duration_seconds=59,
            tags=["Jesus", "prayer", "anxiety", "scripture"],
        ),
    ]
    return upsert_youtube_candidates(db, samples)


def trusted_influencer_boost(video: models.Video) -> float:
    topics = set(video.topics or [])
    creator_profile = video.creator.theology_profile if video.creator else None
    creator_is_trusted = bool(
        isinstance(creator_profile, dict) and creator_profile.get("trusted_influencer")
    )

    if TRUSTED_INFLUENCER_TOPIC in topics or creator_is_trusted:
        return TRUSTED_INFLUENCER_BOOST
    if topics.intersection(set(ALIGNED_SOURCE_TOPICS.values())):
        return TRUSTED_INFLUENCER_BOOST * 0.85
    if PASTOR_CLIPS_TOPIC in topics:
        return TRUSTED_INFLUENCER_BOOST * 0.7
    return 0


def interest_profile_from_topics(preferred_topics: set[str] | None = None) -> UserInterestProfile:
    profile = UserInterestProfile()
    for topic in preferred_topics or set():
        normalized = normalize_topic(topic)
        bump_weight(profile.topic_weights, normalized, 0.15, TOPIC_WEIGHT_MIN, TOPIC_WEIGHT_MAX)
    return profile


def user_interest_profile(db: Session, user: models.User) -> UserInterestProfile:
    profile = UserInterestProfile()

    preference = db.scalar(
        select(models.OnboardingPreference).where(models.OnboardingPreference.user_id == user.id)
    )
    for topic in preference.topics if preference else []:
        bump_weight(
            profile.topic_weights,
            normalize_topic(topic),
            0.14,
            TOPIC_WEIGHT_MIN,
            TOPIC_WEIGHT_MAX,
        )

    follows = db.scalars(select(models.Follow).where(models.Follow.user_id == user.id))
    for follow in follows:
        if follow.target_type == "topic":
            bump_weight(
                profile.topic_weights,
                normalize_topic(follow.target_id),
                0.18,
                TOPIC_WEIGHT_MIN,
                TOPIC_WEIGHT_MAX,
            )
        elif follow.target_type == "creator":
            bump_weight(
                profile.creator_weights,
                follow.target_id,
                0.18,
                CREATOR_WEIGHT_MIN,
                CREATOR_WEIGHT_MAX,
            )

    liked_videos = db.scalars(
        select(models.Video)
        .options(joinedload(models.Video.creator))
        .join(models.Like, models.Like.video_id == models.Video.id)
        .where(models.Like.user_id == user.id)
    )
    for video in liked_videos:
        apply_video_feedback(profile, video, topic_delta=0.10, creator_delta=0.08)

    saved_videos = db.scalars(
        select(models.Video)
        .options(joinedload(models.Video.creator))
        .join(models.Save, models.Save.video_id == models.Video.id)
        .where(models.Save.user_id == user.id)
    )
    for video in saved_videos:
        apply_video_feedback(profile, video, topic_delta=0.12, creator_delta=0.10)

    not_interested_videos = db.scalars(
        select(models.Video)
        .options(joinedload(models.Video.creator))
        .join(models.NotInterested, models.NotInterested.video_id == models.Video.id)
        .where(models.NotInterested.user_id == user.id)
    )
    for video in not_interested_videos:
        apply_video_feedback(profile, video, topic_delta=-0.26, creator_delta=-0.16)

    watch_rows = db.execute(
        select(models.WatchEvent, models.Video)
        .join(models.Video, models.Video.id == models.WatchEvent.video_id)
        .options(joinedload(models.Video.creator))
        .where(models.WatchEvent.user_id == user.id)
    )
    watched_video_signals: dict[str, tuple[models.Video, float]] = {}
    for watch_event, video in watch_rows:
        event_type = watch_event.event_type.lower()
        if event_type == "skip" or (
            watch_event.percent_complete < 0.2 and watch_event.seconds_watched <= 5
        ):
            signal = -0.08
        else:
            completion_signal = 0.035 if watch_event.percent_complete >= 0.75 else 0
            rewatch_signal = 0.025 if watch_event.rewatched else 0
            watch_time_signal = min(watch_event.seconds_watched, 180) / 180 * 0.025
            signal = completion_signal + rewatch_signal + watch_time_signal

        _, previous_signal = watched_video_signals.get(video.id, (video, 0))
        if abs(signal) > abs(previous_signal):
            watched_video_signals[video.id] = (video, signal)

    for video, signal in watched_video_signals.values():
        apply_video_feedback(profile, video, topic_delta=signal, creator_delta=signal * 0.45)

    return profile


def coerce_interest_profile(
    profile_or_topics: UserInterestProfile | set[str] | dict[str, float] | None,
) -> UserInterestProfile:
    if profile_or_topics is None:
        return UserInterestProfile()
    if isinstance(profile_or_topics, UserInterestProfile):
        return profile_or_topics
    if isinstance(profile_or_topics, dict):
        return UserInterestProfile(
            topic_weights={
                normalize_topic(topic): weight
                for topic, weight in profile_or_topics.items()
                if normalize_topic(topic)
            }
        )
    return interest_profile_from_topics(profile_or_topics)


def ranking_score(
    video: models.Video,
    preferred_topics: UserInterestProfile | set[str] | dict[str, float] | None = None,
) -> float:
    profile = coerce_interest_profile(preferred_topics)
    topic_affinity = clamp(
        sum(profile.topic_weights.get(topic, 0) for topic in video_topic_set(video)),
        RANK_TOPIC_SIGNAL_MIN,
        RANK_TOPIC_SIGNAL_MAX,
    )
    creator_affinity = clamp(
        profile.creator_weights.get(video.creator_id, 0),
        RANK_CREATOR_SIGNAL_MIN,
        RANK_CREATOR_SIGNAL_MAX,
    )
    fit_boost = reel_fit_score(video.duration_seconds, video.title, video.description, video.tags)
    return (
        video.spiritual_score * 0.32
        + video.theology_score * 0.25
        + video.entertainment_score * 0.10
        + video.freshness_score * 0.09
        + fit_boost * 0.09
        + trusted_influencer_boost(video)
        + topic_affinity
        + creator_affinity
    )


def creator_cap_for_limit(limit: int) -> int:
    return max(2, ceil(limit * MAX_CREATOR_SHARE))


def diversity_adjusted_score(
    video: models.Video,
    base_score: float,
    creator_counts: Counter[str],
    topic_counts: Counter[str],
) -> float:
    topics = video_topic_set(video)
    repeated_topic_count = sum(topic_counts[topic] for topic in topics)
    has_new_topic = bool(topics) and any(topic_counts[topic] == 0 for topic in topics)

    return (
        base_score
        - creator_counts[video.creator_id] * CREATOR_REPEAT_PENALTY
        - min(repeated_topic_count, 4) * TOPIC_REPEAT_PENALTY
        + (NEW_CREATOR_BONUS if creator_counts[video.creator_id] == 0 else 0)
        + (NEW_TOPIC_BONUS if has_new_topic else 0)
    )


def creator_has_available_alternative(
    remaining: list[tuple[models.Video, float]],
    creator_id: str,
    creator_counts: Counter[str],
    creator_cap: int,
) -> bool:
    return any(
        video.creator_id != creator_id and creator_counts[video.creator_id] < creator_cap
        for video, _ in remaining
    )


def diversify_ranked_videos(
    videos: list[models.Video],
    interest_profile: UserInterestProfile,
    limit: int,
) -> list[models.Video]:
    remaining = [(video, ranking_score(video, interest_profile)) for video in videos]
    selected: list[models.Video] = []
    creator_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    creator_cap = creator_cap_for_limit(limit)

    while remaining and len(selected) < limit:
        best_index: int | None = None
        best_score = float("-inf")

        for index, (video, base_score) in enumerate(remaining):
            has_creator_alternative = creator_has_available_alternative(
                remaining, video.creator_id, creator_counts, creator_cap
            )
            if creator_counts[video.creator_id] >= creator_cap and has_creator_alternative:
                continue
            if selected and selected[-1].creator_id == video.creator_id and has_creator_alternative:
                continue

            candidate_score = diversity_adjusted_score(
                video, base_score, creator_counts, topic_counts
            )
            if candidate_score > best_score:
                best_index = index
                best_score = candidate_score

        if best_index is None:
            best_index = max(
                range(len(remaining)),
                key=lambda index: diversity_adjusted_score(
                    remaining[index][0],
                    remaining[index][1],
                    creator_counts,
                    topic_counts,
                ),
            )

        video, _ = remaining.pop(best_index)
        selected.append(video)
        creator_counts[video.creator_id] += 1
        topic_counts.update(video_topic_set(video))

    return selected


def feed_for_user(db: Session, user: models.User, limit: int) -> list[models.Video]:
    interest_profile = user_interest_profile(db, user)

    hidden_video_ids = select(models.NotInterested.video_id).where(
        models.NotInterested.user_id == user.id
    )
    impression_video_ids = select(models.FeedImpression.video_id).where(
        models.FeedImpression.user_id == user.id
    )
    watched_video_ids = select(models.WatchEvent.video_id).where(
        models.WatchEvent.user_id == user.id
    )
    liked_video_ids = select(models.Like.video_id).where(models.Like.user_id == user.id)
    saved_video_ids = select(models.Save.video_id).where(models.Save.user_id == user.id)
    blocked_creator_ids = select(models.Block.target_id).where(
        and_(models.Block.user_id == user.id, models.Block.target_type == "creator")
    )

    videos = list(
        db.scalars(
            select(models.Video)
            .options(joinedload(models.Video.creator))
            .where(models.Video.moderation_status == "approved")
            .where(models.Video.is_embeddable.is_(True))
            .where(models.Video.id.not_in(hidden_video_ids))
            .where(models.Video.id.not_in(impression_video_ids))
            .where(models.Video.id.not_in(watched_video_ids))
            .where(models.Video.id.not_in(liked_video_ids))
            .where(models.Video.id.not_in(saved_video_ids))
            .where(models.Video.creator_id.not_in(blocked_creator_ids))
        )
    )

    return diversify_ranked_videos(videos, interest_profile, limit)


def should_insert_reflection(db: Session, user: models.User) -> bool:
    recent_watch_seconds = db.scalar(
        select(func.coalesce(func.sum(models.WatchEvent.seconds_watched), 0)).where(
            models.WatchEvent.user_id == user.id
        )
    )
    previous_cards = db.scalar(
        select(func.count(models.ReflectionEvent.id)).where(
            models.ReflectionEvent.user_id == user.id
        )
    )
    return recent_watch_seconds >= 600 and previous_cards == 0


def create_reflection_card(db: Session, user: models.User, triggered_by: str) -> ReflectionCard:
    prompt = "What is one concrete way your next task can be done for Christ?"
    event = models.ReflectionEvent(
        user_id=user.id,
        card_type="scripture",
        title="Pause before the next scroll",
        scripture_ref="Colossians 3:23",
        body=(
            "Whatever you do, work heartily, as for the Lord and not for men. "
            "Take ten seconds, breathe, and ask Christ to make your next task faithful."
        ),
        triggered_by=triggered_by,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return ReflectionCard(
        id=event.id,
        card_type=event.card_type,
        title=event.title,
        scripture_reference=event.scripture_ref,
        body=event.body,
        prompt=prompt,
        trigger=event.triggered_by,
    )


def report_target(
    db: Session,
    reporter_id: str,
    target_type: str,
    target_id: str,
    reason: str,
    details: str | None,
) -> models.ModerationReport:
    report = models.ModerationReport(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        details=details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def apply_moderation(
    db: Session,
    admin: models.User,
    target_type: str,
    target_id: str,
    status: str,
    notes: str | None,
) -> None:
    if target_type == "video":
        target = db.get(models.Video, target_id)
        if target:
            target.moderation_status = status
    elif target_type == "comment":
        target = db.get(models.Comment, target_id)
        if target:
            target.moderation_status = status
    elif target_type == "report":
        target = db.get(models.ModerationReport, target_id)
        if target:
            target.status = status
            target.reviewed_at = datetime.now(UTC)
    elif target_type == "creator":
        target = db.get(models.Creator, target_id)
        if target:
            target.status = status
    elif target_type == "user":
        target = db.get(models.User, target_id)
        if target:
            if status in {"active", "reinstated", "restore"}:
                target.suspended_at = None
            else:
                target.suspended_at = datetime.now(UTC)
                db.query(models.UserSession).filter(models.UserSession.user_id == target_id).update(
                    {"revoked_at": datetime.now(UTC)}
                )
    db.add(
        models.AdminAudit(
            admin_id=admin.id,
            action=f"moderate:{status}",
            target_type=target_type,
            target_id=target_id,
            notes=notes,
        )
    )
    db.commit()


def search(
    db: Session, query: str
) -> tuple[list[models.Creator], list[models.Video], list[models.Topic]]:
    like_query = f"%{query}%"
    creators = list(
        db.scalars(
            select(models.Creator)
            .where(
                or_(
                    models.Creator.display_name.ilike(like_query),
                    models.Creator.handle.ilike(like_query),
                )
            )
            .limit(10)
        )
    )
    videos = list(
        db.scalars(
            select(models.Video)
            .options(joinedload(models.Video.creator))
            .where(
                and_(
                    models.Video.moderation_status == "approved",
                    or_(
                        models.Video.title.ilike(like_query),
                        models.Video.description.ilike(like_query),
                    ),
                )
            )
            .limit(20)
        )
    )
    topic_rows = db.scalars(
        select(models.Topic)
        .where(or_(models.Topic.slug.ilike(like_query), models.Topic.name.ilike(like_query)))
        .limit(10)
    )
    return creators, videos, list(topic_rows)
