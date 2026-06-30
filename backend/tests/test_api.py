from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import evals, models
from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.schemas import YouTubeCandidate
from app.services import TRUSTED_INFLUENCER_TOPIC, classify_candidate, ranking_score, reel_fit_score
from app.youtube import YouTubeAPIError, parse_datetime, parse_duration
from app.youtube_worker import build_ingest_query_plan, should_stop_cycle_for_youtube_error

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


client = TestClient(app)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(email: str = "ryan@example.com") -> tuple[str, dict]:
    response = client.post(
        "/biblemaxxing/api/v1/auth/register",
        json={
            "username": "ryan" if email == "ryan@example.com" else email.split("@")[0],
            "email": email,
            "password": "password123",
            "birthday": "2005-01-01",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["access_token"], payload["user"]


def add_creator(db: Session, creator_id: str, display_name: str) -> models.Creator:
    creator = models.Creator(
        id=creator_id,
        handle=f"@{creator_id}",
        display_name=display_name,
        youtube_channel_id=f"channel-{creator_id}",
    )
    db.add(creator)
    return creator


def add_video(
    db: Session,
    video_id: str,
    creator: models.Creator,
    title: str,
    topics: list[str],
    spiritual_score: float = 0.7,
    theology_score: float = 0.75,
    entertainment_score: float = 0.55,
    freshness_score: float = 0.5,
) -> models.Video:
    video = models.Video(
        id=video_id,
        creator_id=creator.id,
        creator=creator,
        youtube_video_id=f"yt-{video_id}",
        title=title,
        description="A Christian short for recommender testing.",
        thumbnail_url="https://i.ytimg.com/vi/test/hqdefault.jpg",
        duration_seconds=59,
        source_url=f"https://www.youtube.com/shorts/yt-{video_id}",
        embed_url=f"https://www.youtube.com/embed/yt-{video_id}",
        tags=topics,
        topics=topics,
        spiritual_score=spiritual_score,
        theology_score=theology_score,
        entertainment_score=entertainment_score,
        freshness_score=freshness_score,
    )
    db.add(video)
    return video


def feed_video_items(token: str, limit: int = 20) -> list[dict]:
    response = client.get(
        f"/biblemaxxing/api/v1/feed?limit={limit}", headers=auth_headers(token)
    )
    assert response.status_code == 200, response.text
    return [item for item in response.json()["items"] if item["type"] == "video"]


def feed_video_ids(token: str, limit: int = 20) -> list[str]:
    return [item["video"]["id"] for item in feed_video_items(token, limit)]


def test_health() -> None:
    response = client.get("/biblemaxxing/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_youtube_player_page_sets_embed_identity_and_error_handling() -> None:
    response = client.get("/biblemaxxing/player/M7lc1UVf-VE?autoplay=1")
    assert response.status_code == 200
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    body = response.text
    assert "https://www.youtube.com/iframe_api" in body
    assert "origin: window.location.origin" in body
    assert "widget_referrer: window.location.href" in body
    assert "controls: 0" in body
    assert "loop: 1" in body
    assert "playlist: videoID" in body
    assert "YT.PlayerState.ENDED" in body
    assert "near_end_poll" in body
    assert "pointer-events: none" in body
    assert "onPlayerError" in body
    assert "window.webkit.messageHandlers.bibleMaxxingPlayer" in body
    assert "download" not in body.lower()

    invalid = client.get("/biblemaxxing/player/not-a-real-youtube-video-id")
    assert invalid.status_code == 400


def test_youtube_metadata_parsers() -> None:
    assert parse_duration("PT1M05S") == 65
    assert parse_duration("PT2H3M4S") == 7384
    assert parse_duration(None) is None
    assert parse_datetime("2026-06-30T12:34:56Z") is not None


def test_reel_fit_prefers_shorts_without_banning_landscape() -> None:
    vertical_hint = reel_fit_score(58, "Bible verse for today #shorts", "", [])
    useful_landscape = reel_fit_score(164, "Morning prayer to start your day", "", [])

    assert vertical_hint > useful_landscape
    assert useful_landscape > 0


def test_pastor_clip_source_can_pass_christian_filter() -> None:
    candidate = YouTubeCandidate(
        youtube_video_id="pastorclip1",
        title="The True Church | Acts 2:42-47 | Philip Anthony Mitchell",
        description="A sermon clip from a Bible-centered message.",
        channel_id="channel-2819",
        channel_title="2819 Church",
        duration_seconds=59,
        tags=[],
    )

    approved, topics, spiritual_score, theology_score = classify_candidate(candidate)

    assert approved is True
    assert TRUSTED_INFLUENCER_TOPIC in topics
    assert "pastor-clips" in topics
    assert "philip-anthony-mitchell" in topics
    assert spiritual_score > 0.5
    assert theology_score > 0.6


def test_trusted_influencer_content_gets_bounded_ranking_boost() -> None:
    creator = models.Creator(
        id="trusted-creator",
        handle="@2819-church",
        display_name="2819 Church",
        youtube_channel_id="channel-2819",
        theology_profile={"trusted_influencer": True},
    )
    trusted = models.Video(
        id="trusted-video",
        creator_id=creator.id,
        creator=creator,
        youtube_video_id="trusted1",
        title="Walk with Christ at work",
        description="A sermon clip.",
        source_url="https://www.youtube.com/shorts/trusted1",
        embed_url="https://www.youtube.com/embed/trusted1",
        duration_seconds=59,
        tags=[],
        topics=[TRUSTED_INFLUENCER_TOPIC, "pastor-clips", "philip-anthony-mitchell"],
        spiritual_score=0.7,
        theology_score=0.75,
        entertainment_score=0.55,
        freshness_score=0.5,
    )
    ordinary = models.Video(
        id="ordinary-video",
        creator_id="ordinary-creator",
        youtube_video_id="ordinary1",
        title="Walk with Christ at work",
        description="A good Christian short.",
        source_url="https://www.youtube.com/shorts/ordinary1",
        embed_url="https://www.youtube.com/embed/ordinary1",
        duration_seconds=59,
        tags=[],
        topics=["christian", "workplace"],
        spiritual_score=0.7,
        theology_score=0.75,
        entertainment_score=0.55,
        freshness_score=0.5,
    )

    assert ranking_score(trusted) > ranking_score(ordinary)
    assert ranking_score(trusted) - ranking_score(ordinary) < 0.3


def test_feed_learns_different_user_interests_from_feedback() -> None:
    prayer_token, _ = register_user("prayer@example.com")
    apologetics_token, _ = register_user("apologetics@example.com")

    with TestingSessionLocal() as db:
        prayer_creator = add_creator(db, "prayer-creator", "Prayer Pastor")
        apologetics_creator = add_creator(db, "apologetics-creator", "Apologetics Teacher")
        add_video(db, "prayer-seed", prayer_creator, "How to pray at work", ["prayer"])
        add_video(
            db,
            "apologetics-seed",
            apologetics_creator,
            "Defending the resurrection",
            ["apologetics"],
        )
        add_video(db, "prayer-next", prayer_creator, "Pray before your next task", ["prayer"])
        add_video(
            db,
            "apologetics-next",
            apologetics_creator,
            "Why the resurrection matters",
            ["apologetics"],
        )
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/onboarding",
            headers=auth_headers(prayer_token),
            json={"topicSlugs": ["Prayer"], "intensity": "balanced"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/onboarding",
            headers=auth_headers(apologetics_token),
            json={"topicSlugs": ["Apologetics"], "intensity": "balanced"},
        ).status_code
        == 200
    )

    assert (
        client.post(
            "/biblemaxxing/api/v1/topics/prayer/follow", headers=auth_headers(prayer_token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/creators/prayer-creator/follow",
            headers=auth_headers(prayer_token),
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/topics/apologetics/follow",
            headers=auth_headers(apologetics_token),
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/creators/apologetics-creator/follow",
            headers=auth_headers(apologetics_token),
        ).status_code
        == 200
    )

    for token, video_id in (
        (prayer_token, "prayer-seed"),
        (apologetics_token, "apologetics-seed"),
    ):
        assert (
            client.post(
                f"/biblemaxxing/api/v1/videos/{video_id}/like", headers=auth_headers(token)
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/biblemaxxing/api/v1/videos/{video_id}/save", headers=auth_headers(token)
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/biblemaxxing/api/v1/videos/{video_id}/watch",
                headers=auth_headers(token),
                json={"secondsWatched": 80, "percentComplete": 1, "rewatched": True},
            ).status_code
            == 200
        )

    prayer_feed = feed_video_ids(prayer_token)
    apologetics_feed = feed_video_ids(apologetics_token)

    assert prayer_feed.index("prayer-next") < prayer_feed.index("apologetics-next")
    assert apologetics_feed.index("apologetics-next") < apologetics_feed.index("prayer-next")
    assert "prayer-seed" not in prayer_feed
    assert "apologetics-seed" not in apologetics_feed


def test_feed_balances_trusted_creator_relevance_with_diversity() -> None:
    token, _ = register_user("diversity@example.com")

    with TestingSessionLocal() as db:
        philip = add_creator(db, "philip", "Philip Anthony Mitchell")
        philip.theology_profile = {"trusted_influencer": True}
        bryce = add_creator(db, "bryce", "Bryce Crawford")
        bible_project = add_creator(db, "bibleproject", "BibleProject")
        cliffe = add_creator(db, "cliffe", "Cliffe Knechtle")
        gavin = add_creator(db, "gavin", "Gavin Ortlund")
        tim = add_creator(db, "tim", "Tim Keller")
        david = add_creator(db, "david", "David Platt")

        for index in range(1, 8):
            add_video(
                db,
                f"philip-{index}",
                philip,
                f"Philip sermon clip {index}",
                ["trusted-influencer", "pastor-clips", "philip-anthony-mitchell", "sermon"],
                spiritual_score=0.86,
                theology_score=0.86,
                entertainment_score=0.7,
                freshness_score=0.7,
            )

        add_video(db, "bryce-1", bryce, "Workplace holiness", ["workplace", "discipleship"])
        add_video(db, "bibleproject-1", bible_project, "Scripture theme", ["bible", "scripture"])
        add_video(db, "cliffe-1", cliffe, "Apologetics answer", ["apologetics", "gospel"])
        add_video(db, "gavin-1", gavin, "Church history context", ["theology", "church"])
        add_video(db, "tim-1", tim, "Gospel and work", ["gospel", "workplace"])
        add_video(db, "david-1", david, "Prayer for the nations", ["prayer", "missions"])
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/onboarding",
            headers=auth_headers(token),
            json={"topicSlugs": ["Pastor Clips", "Discipleship"], "intensity": "balanced"},
        ).status_code
        == 200
    )
    assert (
        client.post("/biblemaxxing/api/v1/creators/philip/follow", headers=auth_headers(token))
        .status_code
        == 200
    )

    items = feed_video_items(token, limit=8)
    creator_ids = [item["video"]["creator"]["id"] for item in items]
    topics = {topic for item in items for topic in item["video"]["topics"]}

    assert len(items) == 8
    assert creator_ids.count("philip") <= 2
    assert len(set(creator_ids)) >= 4
    assert all(left != right for left, right in zip(creator_ids, creator_ids[1:], strict=False))
    assert {"workplace", "bible", "apologetics"}.issubset(topics)
    assert "philip-1" in [item["video"]["id"] for item in items[:3]]


def test_feed_limits_same_preacher_across_repost_channels() -> None:
    token, _ = register_user("source-diversity@example.com")

    with TestingSessionLocal() as db:
        for index in range(1, 8):
            creator = add_creator(db, f"philip-repost-{index}", f"Philip Repost Channel {index}")
            add_video(
                db,
                f"philip-repost-video-{index}",
                creator,
                f"Philip Anthony Mitchell repost {index}",
                ["trusted-influencer", "pastor-clips", "philip-anthony-mitchell", "sermon"],
                spiritual_score=0.88,
                theology_score=0.88,
                entertainment_score=0.75,
                freshness_score=0.75,
            )

        alternatives = [
            ("bibleproject", "BibleProject", "bibleproject-clip", ["bibleproject", "scripture"]),
            ("bryce", "Bryce Crawford", "bryce-clip", ["bryce-crawford", "testimony"]),
            ("cliffe", "Cliffe Knechtle", "cliffe-clip", ["cliffe-knechtle", "apologetics"]),
            ("gavin", "Gavin Ortlund", "gavin-clip", ["gavin-ortlund", "theology"]),
            ("tim", "Tim Keller", "tim-clip", ["tim-keller", "gospel"]),
            ("prayer", "Prayer Teacher", "prayer-clip", ["prayer"]),
            ("discipline", "Discipline Teacher", "discipline-clip", ["discipline"]),
            ("workplace", "Workplace Faith", "workplace-clip", ["workplace"]),
        ]
        for creator_id, name, video_id, topics in alternatives:
            creator = add_creator(db, creator_id, name)
            add_video(db, video_id, creator, f"{name} video", topics)
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/onboarding",
            headers=auth_headers(token),
            json={"topicSlugs": ["Pastor Clips"], "intensity": "balanced"},
        ).status_code
        == 200
    )

    items = feed_video_items(token, limit=8)
    philip_count = sum(
        "philip-anthony-mitchell" in item["video"]["topics"] for item in items
    )
    source_sequences = [
        "philip" if "philip-anthony-mitchell" in item["video"]["topics"] else "other"
        for item in items
    ]

    assert len(items) == 8
    assert philip_count <= 1
    assert "philip" in source_sequences
    assert source_sequences.count("other") >= 6
    assert all(
        not (left == right == "philip")
        for left, right in zip(source_sequences, source_sequences[1:], strict=False)
    )


def test_recommendation_eval_flags_single_source_dominance() -> None:
    philip_creator = models.Creator(
        id="philip-eval-creator",
        handle="@philip-eval",
        display_name="Philip Eval",
        youtube_channel_id="channel-philip-eval",
    )
    other_creator = models.Creator(
        id="other-eval-creator",
        handle="@other-eval",
        display_name="Other Eval",
        youtube_channel_id="channel-other-eval",
    )
    videos = [
        models.Video(
            id=f"philip-eval-{index}",
            creator_id=philip_creator.id,
            creator=philip_creator,
            youtube_video_id=f"philip-eval-{index}",
            title=f"Philip clip {index}",
            description="A sermon clip.",
            source_url=f"https://www.youtube.com/shorts/philip-eval-{index}",
            embed_url=f"https://www.youtube.com/embed/philip-eval-{index}",
            duration_seconds=59,
            tags=[],
            topics=["trusted-influencer", "pastor-clips", "philip-anthony-mitchell"],
            spiritual_score=0.9,
            theology_score=0.9,
            entertainment_score=0.7,
            freshness_score=0.7,
        )
        for index in range(5)
    ]
    videos.append(
        models.Video(
            id="other-eval-1",
            creator_id=other_creator.id,
            creator=other_creator,
            youtube_video_id="other-eval-1",
            title="Other faithful clip",
            description="A Bible clip.",
            source_url="https://www.youtube.com/shorts/other-eval-1",
            embed_url="https://www.youtube.com/embed/other-eval-1",
            duration_seconds=59,
            tags=[],
            topics=["discipleship"],
            spiritual_score=0.9,
            theology_score=0.9,
            entertainment_score=0.7,
            freshness_score=0.7,
        )
    )

    scorecard = evals.evaluate_recommendation_feed(videos, limit=6)

    assert scorecard.status == "regressed"
    assert scorecard.gates["source_not_dominant"] is False
    assert scorecard.metrics["max_source_share"] > 0.35


def test_recommendation_eval_scores_diverse_high_quality_feed_healthy() -> None:
    videos = []
    for index, topic in enumerate(
        ["prayer", "discipleship", "bible", "workplace", "apologetics", "worship"], start=1
    ):
        creator = models.Creator(
            id=f"eval-creator-{index}",
            handle=f"@eval-{index}",
            display_name=f"Eval Creator {index}",
            youtube_channel_id=f"channel-eval-{index}",
        )
        videos.append(
            models.Video(
                id=f"eval-video-{index}",
                creator_id=creator.id,
                creator=creator,
                youtube_video_id=f"eval-video-{index}",
                title=f"Faithful {topic} short #shorts",
                description="Bible-centered Christian encouragement.",
                source_url=f"https://www.youtube.com/shorts/eval-video-{index}",
                embed_url=f"https://www.youtube.com/embed/eval-video-{index}",
                duration_seconds=58,
                tags=[topic],
                topics=[topic],
                spiritual_score=0.9,
                theology_score=0.9,
                entertainment_score=0.7,
                freshness_score=0.7,
            )
        )

    scorecard = evals.evaluate_recommendation_feed(videos, limit=6)

    assert scorecard.status == "healthy"
    assert scorecard.metrics["creator_coverage"] == 1
    assert all(scorecard.gates.values())


def test_ingest_eval_rejects_red_team_heretical_fixtures() -> None:
    scorecard = evals.evaluate_red_team_ingestion()

    assert scorecard.gates["no_red_flag_auto_approved"] is True
    assert scorecard.metrics["red_flag_candidate_count"] == 5
    assert scorecard.metrics["red_flag_auto_approved_count"] == 0
    assert scorecard.metrics["accepted_new_count"] == 1
    assert scorecard.metrics["rejected_by_filter_count"] >= 5


def test_query_plan_eval_requires_broad_and_pastor_lanes() -> None:
    settings = Settings(
        _env_file=None,
        youtube_ingest_queries="general one|general two",
        youtube_ingest_pastor_queries="pastor one|pastor two",
        youtube_ingest_pastor_queries_per_cycle=1,
        youtube_ingest_search_calls_per_cycle=3,
        youtube_ingest_daily_search_call_budget=36,
    )

    healthy = evals.evaluate_query_plan(settings, ["general one", "general two", "pastor one"])
    missing_pastor = evals.evaluate_query_plan(settings, ["general one", "general two"])
    over_budget = evals.evaluate_query_plan(
        settings, ["general one", "general two", "pastor one", "pastor two"]
    )

    assert healthy.gates["has_broad_discovery_lane"] is True
    assert healthy.gates["has_pastor_source_lane"] is True
    assert healthy.gates["within_cycle_search_budget"] is True
    assert healthy.gates["within_daily_search_budget"] is True
    assert missing_pastor.status == "regressed"
    assert missing_pastor.gates["has_pastor_source_lane"] is False
    assert over_budget.status == "regressed"
    assert over_budget.gates["within_cycle_search_budget"] is False


def test_negative_feedback_downranks_related_videos_without_affecting_other_users() -> None:
    token, _ = register_user("negative@example.com")
    other_token, _ = register_user("other-negative@example.com")

    with TestingSessionLocal() as db:
        worship_creator = add_creator(db, "worship-creator", "Worship Channel")
        discipline_creator = add_creator(db, "discipline-creator", "Discipline Channel")
        add_video(db, "worship-rejected", worship_creator, "Worship clip", ["worship"])
        add_video(db, "worship-next", worship_creator, "Another worship clip", ["worship"])
        add_video(db, "discipline-next", discipline_creator, "Discipline in Christ", ["discipline"])
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/worship-rejected/not-interested",
            headers=auth_headers(token),
            json={"reason": "not my topic"},
        ).status_code
        == 200
    )

    user_feed = feed_video_ids(token)
    other_feed = feed_video_ids(other_token)

    assert "worship-rejected" not in user_feed
    assert "worship-rejected" in other_feed
    assert user_feed.index("discipline-next") < user_feed.index("worship-next")


def test_seen_history_exclusions_are_per_signal_and_per_user() -> None:
    token, _ = register_user("seen@example.com")
    other_token, _ = register_user("seen-other@example.com")

    with TestingSessionLocal() as db:
        creator = add_creator(db, "seen-creator", "Seen History Channel")
        for video_id in (
            "impression-seen",
            "watch-seen",
            "like-seen",
            "save-seen",
            "not-interested-seen",
            "still-new",
        ):
            add_video(db, video_id, creator, f"{video_id} title", ["discipleship"])
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/feed/impressions",
            headers=auth_headers(token),
            json={"videoID": "impression-seen", "position": 0},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/watch-seen/watch",
            headers=auth_headers(token),
            json={"secondsWatched": 15, "percentComplete": 0.5},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/like-seen/like", headers=auth_headers(token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/save-seen/save", headers=auth_headers(token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/not-interested-seen/not-interested",
            headers=auth_headers(token),
            json={"reason": "not interested"},
        ).status_code
        == 200
    )

    user_feed = set(feed_video_ids(token))
    other_feed = set(feed_video_ids(other_token))
    excluded_ids = {
        "impression-seen",
        "watch-seen",
        "like-seen",
        "save-seen",
        "not-interested-seen",
    }

    assert excluded_ids.isdisjoint(user_feed)
    assert excluded_ids.issubset(other_feed)
    assert "still-new" in user_feed


def test_watch_time_feedback_is_bounded_by_spiritual_and_theological_quality() -> None:
    token, _ = register_user("bounded-watch@example.com")

    with TestingSessionLocal() as db:
        viral_creator = add_creator(db, "viral-creator", "Viral Clips")
        safe_creator = add_creator(db, "safe-creator", "Faithful Bible Teaching")
        add_video(
            db,
            "viral-signal",
            viral_creator,
            "A flashy Christian clip",
            ["viral"],
            spiritual_score=0.35,
            theology_score=0.4,
            entertainment_score=0.9,
            freshness_score=0.9,
        )
        add_video(
            db,
            "viral-next",
            viral_creator,
            "Another flashy Christian clip",
            ["viral"],
            spiritual_score=0.35,
            theology_score=0.4,
            entertainment_score=0.9,
            freshness_score=0.9,
        )
        add_video(
            db,
            "safe-next",
            safe_creator,
            "Faithful Scripture for work",
            ["discipleship"],
            spiritual_score=0.9,
            theology_score=0.9,
            entertainment_score=0.45,
            freshness_score=0.5,
        )
        db.commit()

    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/viral-signal/watch",
            headers=auth_headers(token),
            json={"secondsWatched": 9999, "percentComplete": 1, "rewatched": True},
        ).status_code
        == 200
    )

    video_ids = feed_video_ids(token)

    assert "viral-signal" not in video_ids
    assert video_ids.index("safe-next") < video_ids.index("viral-next")


def test_feedback_endpoints_reject_unknown_videos() -> None:
    token, _ = register_user("invalid-feedback@example.com")
    headers = auth_headers(token)

    assert (
        client.post("/biblemaxxing/api/v1/videos/missing/like", headers=headers).status_code
        == 404
    )
    assert (
        client.post("/biblemaxxing/api/v1/videos/missing/save", headers=headers).status_code
        == 404
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/missing/not-interested",
            headers=headers,
            json={"reason": "missing"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/videos/missing/watch",
            headers=headers,
            json={"secondsWatched": 1, "percentComplete": 0.1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/feed/impressions",
            headers=headers,
            json={"videoID": "missing", "position": 0},
        ).status_code
        == 404
    )


def test_worker_rotates_pastor_queries_without_overriding_manual_queries() -> None:
    settings = Settings(
        _env_file=None,
        youtube_ingest_queries="general one|general two",
        youtube_ingest_pastor_queries="pastor one|pastor two|pastor three",
        youtube_ingest_pastor_queries_per_cycle=2,
        youtube_ingest_search_calls_per_cycle=3,
    )

    queries, broad_cursor, pastor_cursor = build_ingest_query_plan(
        settings, broad_query_cursor=0, pastor_query_cursor=0
    )
    assert queries == ["general one", "pastor one", "pastor two"]
    assert broad_cursor == 1
    assert pastor_cursor == 2

    next_queries, next_broad_cursor, next_pastor_cursor = build_ingest_query_plan(
        settings, broad_query_cursor=broad_cursor, pastor_query_cursor=pastor_cursor
    )
    assert next_queries == ["general two", "pastor three", "pastor one"]
    assert next_broad_cursor == 0
    assert next_pastor_cursor == 1

    manual_queries, manual_broad_cursor, manual_pastor_cursor = build_ingest_query_plan(
        settings,
        override_queries=["manual only"],
        broad_query_cursor=broad_cursor,
        pastor_query_cursor=pastor_cursor,
    )
    assert manual_queries == ["manual only"]
    assert manual_broad_cursor == broad_cursor
    assert manual_pastor_cursor == pastor_cursor


def test_worker_stops_current_cycle_on_youtube_quota_errors() -> None:
    quota_error = YouTubeAPIError(
        "YouTube API search failed with 429: quota exceeded",
        status_code=429,
        body="Quota exceeded for quota metric Search Queries",
    )
    transient_error = YouTubeAPIError("temporary YouTube error", status_code=500)

    assert should_stop_cycle_for_youtube_error(quota_error) is True
    assert should_stop_cycle_for_youtube_error(transient_error) is False


def test_admin_eval_runs_persist_and_require_admin_access() -> None:
    admin_token, admin_user = register_user("eval-admin@example.com")
    user_token, _ = register_user("eval-user@example.com")

    with TestingSessionLocal() as db:
        for index in range(4):
            creator = add_creator(db, f"eval-history-creator-{index}", f"Eval Creator {index}")
            add_video(
                db,
                f"eval-history-video-{index}",
                creator,
                f"Faithful discipleship short {index}",
                ["prayer", "discipleship"],
            )
        db.commit()

    assert (
        client.get(
            "/biblemaxxing/api/v1/admin/evals/runs", headers=auth_headers(user_token)
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/biblemaxxing/api/v1/admin/evals/recommendations",
            headers=auth_headers(user_token),
        ).status_code
        == 403
    )

    recommendation_eval = client.get(
        "/biblemaxxing/api/v1/admin/evals/recommendations?limit=3",
        headers=auth_headers(admin_token),
    )
    assert recommendation_eval.status_code == 200, recommendation_eval.text
    recommendation_payload = recommendation_eval.json()
    assert recommendation_payload["saved"] is True
    assert recommendation_payload["saved_run_id"]

    runs = client.get(
        "/biblemaxxing/api/v1/admin/evals/runs?limit=10",
        headers=auth_headers(admin_token),
    )
    assert runs.status_code == 200, runs.text
    saved_run = next(
        run for run in runs.json() if run["id"] == recommendation_payload["saved_run_id"]
    )
    assert saved_run["scorecard_name"] == recommendation_payload["name"]
    assert saved_run["category"] == "recommendation"
    assert saved_run["status"] == recommendation_payload["status"]
    assert saved_run["overall_score"] == recommendation_payload["overall_score"]
    assert saved_run["metrics"]["feed_count"] >= 1
    assert saved_run["gates"] == recommendation_payload["gates"]
    assert saved_run["notes"] == recommendation_payload["notes"]
    assert saved_run["subject_user_id"] == admin_user["id"]
    assert saved_run["source"] == "admin:recommendations"

    unsaved_red_team = client.get(
        "/biblemaxxing/api/v1/admin/evals/ingest/red-team?save=false",
        headers=auth_headers(admin_token),
    )
    assert unsaved_red_team.status_code == 200, unsaved_red_team.text
    assert unsaved_red_team.json()["saved"] is False
    assert unsaved_red_team.json()["saved_run_id"] is None

    runs_after_unsaved = client.get(
        "/biblemaxxing/api/v1/admin/evals/runs?limit=10",
        headers=auth_headers(admin_token),
    )
    assert len(runs_after_unsaved.json()) == 1

    red_team = client.get(
        "/biblemaxxing/api/v1/admin/evals/ingest/red-team",
        headers=auth_headers(admin_token),
    )
    assert red_team.status_code == 200, red_team.text
    assert red_team.json()["saved"] is True

    ingestion_runs = client.get(
        "/biblemaxxing/api/v1/admin/evals/runs?category=ingestion",
        headers=auth_headers(admin_token),
    )
    assert ingestion_runs.status_code == 200, ingestion_runs.text
    assert [run["id"] for run in ingestion_runs.json()] == [red_team.json()["saved_run_id"]]


def test_auth_onboarding_feed_and_interactions() -> None:
    token, user = register_user()
    assert user["is_admin"] is True
    second_token, second_user = register_user("commenter@example.com")

    ingest = client.post(
        "/biblemaxxing/api/v1/admin/ingest/sample",
        headers=auth_headers(token),
    )
    assert ingest.status_code == 200, ingest.text
    assert ingest.json()["created"] >= 1

    onboarding = client.post(
        "/biblemaxxing/api/v1/onboarding",
        headers=auth_headers(token),
        json={
            "topicSlugs": ["Prayer", "Workplace holiness", "Bible study"],
            "intensity": "balanced",
        },
    )
    assert onboarding.status_code == 200, onboarding.text
    assert onboarding.json()["onboarding_completed"] is True

    feed = client.get("/biblemaxxing/api/v1/feed", headers=auth_headers(token))
    assert feed.status_code == 200, feed.text
    items = feed.json()["items"]
    assert items
    video_item = next(item for item in items if item["type"] == "video")
    video_id = video_item["video"]["id"]
    creator_id = video_item["video"]["creator"]["id"]

    recommendation_eval = client.get(
        "/biblemaxxing/api/v1/admin/evals/recommendations?limit=3",
        headers=auth_headers(token),
    )
    assert recommendation_eval.status_code == 200, recommendation_eval.text
    assert recommendation_eval.json()["metrics"]["feed_count"] >= 1

    red_team_eval = client.get(
        "/biblemaxxing/api/v1/admin/evals/ingest/red-team",
        headers=auth_headers(token),
    )
    assert red_team_eval.status_code == 200, red_team_eval.text
    assert red_team_eval.json()["metrics"]["red_flag_auto_approved_count"] == 0

    assert (
        client.post(
            f"/biblemaxxing/api/v1/videos/{video_id}/like", headers=auth_headers(token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/biblemaxxing/api/v1/videos/{video_id}/save", headers=auth_headers(token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/biblemaxxing/api/v1/watch-events",
            headers=auth_headers(token),
            json={
                "videoID": video_id,
                "feedItemID": "feed-item-test",
                "eventType": "pause",
                "positionSeconds": 12,
                "durationSeconds": 24,
                "autoplay": True,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/biblemaxxing/api/v1/videos/{video_id}/watch",
            headers=auth_headers(token),
            json={
                "seconds_watched": 601,
                "percent_complete": 1,
                "rewatched": True,
                "event_type": "complete",
            },
        ).status_code
        == 200
    )

    reflected_feed = client.get("/biblemaxxing/api/v1/feed", headers=auth_headers(token))
    assert reflected_feed.status_code == 200
    reflected_items = reflected_feed.json()["items"]
    reflection = reflected_items[0]["reflection"]
    assert reflected_items[0]["type"] == "reflection"
    assert reflection["scripture_reference"] == "Colossians 3:23"
    assert reflection["prompt"]
    assert reflection["trigger"]
    assert video_id not in {
        item["video"]["id"] for item in reflected_items if item["type"] == "video"
    }

    comment = client.post(
        f"/biblemaxxing/api/v1/videos/{video_id}/comments",
        headers=auth_headers(token),
        json={"body": "This helped me refocus on Christ at work."},
    )
    assert comment.status_code == 200, comment.text
    comment_id = comment.json()["id"]

    second_comment = client.post(
        f"/biblemaxxing/api/v1/videos/{video_id}/comments",
        headers=auth_headers(second_token),
        json={"body": "Second visible comment."},
    )
    assert second_comment.status_code == 200, second_comment.text

    comments_before_block = client.get(
        f"/biblemaxxing/api/v1/videos/{video_id}/comments", headers=auth_headers(token)
    )
    assert comments_before_block.status_code == 200
    assert len(comments_before_block.json()) == 2

    block_user = client.post(
        f"/biblemaxxing/api/v1/users/{second_user['id']}/block", headers=auth_headers(token)
    )
    assert block_user.status_code == 200, block_user.text

    comments_after_block = client.get(
        f"/biblemaxxing/api/v1/videos/{video_id}/comments", headers=auth_headers(token)
    )
    assert comments_after_block.status_code == 200
    assert len(comments_after_block.json()) == 1

    assert (
        client.post(
            f"/biblemaxxing/api/v1/creators/{creator_id}/block", headers=auth_headers(token)
        ).status_code
        == 200
    )

    report = client.post(
        f"/biblemaxxing/api/v1/comments/{comment_id}/report",
        headers=auth_headers(token),
        json={"reason": "test report", "notes": "moderation flow check"},
    )
    assert report.status_code == 200, report.text

    reports = client.get(
        "/biblemaxxing/api/v1/admin/reports?status=open&type=comment",
        headers=auth_headers(token),
    )
    assert reports.status_code == 200
    assert len(reports.json()) == 1
    report_id = reports.json()[0]["id"]

    assert (
        client.post(
            f"/biblemaxxing/api/v1/admin/reports/{report_id}/resolve",
            headers=auth_headers(token),
            json={"status": "actioned", "notes": "covered by test"},
        ).status_code
        == 200
    )

    moderate = client.patch(
        f"/biblemaxxing/api/v1/admin/comments/{comment_id}/moderation",
        headers=auth_headers(token),
        json={"status": "hidden", "notes": "test hide"},
    )
    assert moderate.status_code == 200, moderate.text

    assert (
        client.patch(
            f"/biblemaxxing/api/v1/admin/creators/{creator_id}",
            headers=auth_headers(token),
            json={"status": "approved", "notes": "creator alias check"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/biblemaxxing/api/v1/admin/users/{second_user['id']}",
            headers=auth_headers(token),
            json={"status": "suspended", "notes": "user alias check"},
        ).status_code
        == 200
    )
    assert (
        client.get("/biblemaxxing/api/v1/admin/users", headers=auth_headers(token)).status_code
        == 200
    )
    assert (
        client.get("/biblemaxxing/api/v1/admin/creators", headers=auth_headers(token)).status_code
        == 200
    )
    blocks = client.get("/biblemaxxing/api/v1/admin/blocks", headers=auth_headers(token))
    assert blocks.status_code == 200
    assert len(blocks.json()) >= 2
    audit = client.get("/biblemaxxing/api/v1/admin/audit-log", headers=auth_headers(token))
    assert audit.status_code == 200
    assert len(audit.json()) >= 4

    assert (
        client.post(
            f"/biblemaxxing/api/v1/videos/{video_id}/not-interested",
            headers=auth_headers(token),
            json={"reason": "not my topic"},
        ).status_code
        == 200
    )


def test_account_deletion_revokes_access() -> None:
    token, _ = register_user("delete@example.com")
    delete = client.delete("/biblemaxxing/api/v1/account", headers=auth_headers(token))
    assert delete.status_code == 200

    me = client.get("/biblemaxxing/api/v1/me", headers=auth_headers(token))
    assert me.status_code == 401

    _, new_user = register_user("new-admin@example.com")
    assert new_user["is_admin"] is True
