from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.youtube import parse_datetime, parse_duration

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
    reflection = reflected_feed.json()["items"][0]["reflection"]
    assert reflected_feed.json()["items"][0]["type"] == "reflection"
    assert reflection["scripture_reference"] == "Colossians 3:23"
    assert reflection["prompt"]
    assert reflection["trigger"]

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
