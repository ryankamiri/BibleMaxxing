import json
import re
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import evals, models, schemas, services
from app.config import get_settings
from app.database import Base, engine, get_db
from app.security import create_access_token, decode_access_token, hash_password, verify_password

settings = get_settings()

app = FastAPI(
    title="BibleMaxxing API",
    version="0.1.0",
    docs_url="/biblemaxxing/docs",
    openapi_url="/biblemaxxing/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer = HTTPBearer(auto_error=False)
API_PREFIX = "/biblemaxxing/api/v1"
YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,20}$")
CONTACT_EMAIL = "ryanamiri05@gmail.com"


@app.on_event("startup")
def on_startup() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)


def issue_auth_response(db: Session, user: models.User) -> schemas.AuthResponse:
    access_token, token_id, expires_at = create_access_token(user.id)
    db.add(models.UserSession(user_id=user.id, token_id=token_id, expires_at=expires_at))
    db.commit()
    db.refresh(user)
    return schemas.AuthResponse(access_token=access_token, user=user)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub") or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    session = db.scalar(
        select(models.UserSession).where(models.UserSession.token_id == payload["jti"])
    )
    if session is None or session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    user = db.get(models.User, payload["sub"])
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")
    if user.suspended_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User suspended")
    return user


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.UserSession:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    session = db.scalar(
        select(models.UserSession).where(models.UserSession.token_id == payload["jti"])
    )
    if session is None or session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    return session


def anonymize_deleted_account(db: Session, user: models.User, deleted_at: datetime) -> None:
    deleted_slug = user.id.replace("-", "")
    user.username = f"deleted-{deleted_slug}"
    user.email = f"deleted+{user.id}@deleted.biblemaxxing.local"
    user.password_hash = hash_password(f"deleted:{user.id}:{deleted_at.isoformat()}")
    user.birthday = None
    user.is_admin = False
    user.onboarding_completed = False
    user.deleted_at = deleted_at

    db.query(models.UserSession).filter(models.UserSession.user_id == user.id).update(
        {"revoked_at": deleted_at}, synchronize_session=False
    )
    db.query(models.OnboardingPreference).filter_by(user_id=user.id).delete(
        synchronize_session=False
    )
    for model in (
        models.FeedImpression,
        models.WatchEvent,
        models.Like,
        models.Save,
        models.NotInterested,
        models.Follow,
        models.Block,
        models.ReflectionEvent,
    ):
        db.query(model).filter_by(user_id=user.id).delete(synchronize_session=False)

    db.query(models.Comment).filter_by(user_id=user.id).update(
        {"body": "[account deleted]", "moderation_status": "deleted_by_user"},
        synchronize_session=False,
    )
    db.query(models.ModerationReport).filter_by(reporter_id=user.id).update(
        {"details": None}, synchronize_session=False
    )
    db.query(models.EvalRun).filter_by(subject_user_id=user.id).update(
        {"subject_user_id": None}, synchronize_session=False
    )


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user


@app.get("/biblemaxxing/health")
def health() -> dict:
    return {"ok": True, "service": "biblemaxxing", "env": settings.env}


def public_page_document(title: str, body: str) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} | BibleMaxxing</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
      background: #050505;
      color: #f8f8f8;
    }}
    body {{
      margin: 0 auto;
      max-width: 760px;
      padding: 44px 20px 64px;
      line-height: 1.55;
    }}
    h1 {{ font-size: clamp(34px, 7vw, 54px); line-height: 0.95; margin: 0 0 12px; }}
    h2 {{ margin-top: 32px; }}
    p, li {{ color: rgba(248, 248, 248, 0.78); }}
    a {{ color: #ffe45e; }}
    .updated {{ color: rgba(248, 248, 248, 0.55); font-size: 14px; margin-bottom: 30px; }}
  </style>
</head>
<body>
  <h1>{safe_title}</h1>
  <p class="updated">Last updated June 30, 2026</p>
  {body}
</body>
</html>"""


@app.get("/biblemaxxing/privacy", response_class=HTMLResponse)
def privacy_page() -> HTMLResponse:
    return HTMLResponse(
        public_page_document(
            "Privacy Policy",
            f"""
  <p>BibleMaxxing is a Christian short-form video app with Bible-centered curation,
  reflection breaks, comments, reports, blocks, and account safety tools.</p>
  <h2>Information We Collect</h2>
  <ul>
    <li>Account details: username, email address, password hash, birthday or age
    posture, and Apple sign-in identifiers when used.</li>
    <li>App activity: onboarding topics, follows, likes, saves, not-interested
    actions, watch events, comments, reports, blocks, and moderation/admin
    actions.</li>
    <li>Content metadata: YouTube video IDs, titles, descriptions, thumbnails,
    creator/channel metadata, topics, and moderation status.</li>
  </ul>
  <h2>How We Use Information</h2>
  <p>We use this information to operate the feed, personalize recommendations,
  secure accounts, moderate comments/content, respond to reports, support account
  deletion, and keep the app spiritually useful and safe.</p>
  <h2>Third-Party Content</h2>
  <p>Videos play through official YouTube embedded playback. BibleMaxxing does not
  download, cache, convert, rehost, or serve YouTube audiovisual content.</p>
  <h2>Your Choices</h2>
  <p>You can delete your account in Settings. You can also report videos/comments
  and block users/creators in the app.</p>
  <h2>Contact</h2>
  <p>For privacy or moderation questions, email
  <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
""",
        )
    )


@app.get("/biblemaxxing/terms", response_class=HTMLResponse)
def terms_page() -> HTMLResponse:
    return HTMLResponse(
        public_page_document(
            "Terms of Service",
            f"""
  <p>By using BibleMaxxing, you agree to use the app lawfully and respectfully.
  BibleMaxxing curates Christian short-form video metadata and plays videos
  through official embedded YouTube playback.</p>
  <h2>Accounts</h2>
  <p>You are responsible for your account activity. Users must be at least 13 years old.</p>
  <h2>Content And Conduct</h2>
  <p>Do not post abusive, profane, hateful, harassing, sexual, violent, spammy,
  deceptive, illegal, or otherwise unsafe comments. We may reject, hide, remove,
  or moderate content that violates these terms or the community guidelines.</p>
  <h2>Third-Party Video</h2>
  <p>YouTube videos remain hosted and controlled by YouTube and their respective
  creators. BibleMaxxing does not claim ownership of third-party videos and does
  not provide offline playback or camera-roll saving for YouTube-sourced videos.</p>
  <h2>Reports, Blocks, And Account Deletion</h2>
  <p>You can report videos/comments, block users/creators, and delete your account
  in the app. Contact <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> for support.</p>
""",
        )
    )


@app.get("/biblemaxxing/community", response_class=HTMLResponse)
def community_page() -> HTMLResponse:
    return HTMLResponse(
        public_page_document(
            "Community Guidelines",
            f"""
  <p>BibleMaxxing exists to encourage Christ-centered attention, Scripture-shaped
  reflection, and thoughtful conversation.</p>
  <h2>Allowed</h2>
  <ul>
    <li>Thoughtful comments about faith, Scripture, repentance, prayer, work, and discipleship.</li>
    <li>Respectful disagreement and questions asked in good faith.</li>
    <li>Reports when content seems unsafe, abusive, non-Christian, or unavailable.</li>
  </ul>
  <h2>Not Allowed</h2>
  <ul>
    <li>Abuse, harassment, slurs, threats, profanity aimed at people, or cruelty.</li>
    <li>Sexual content, graphic violence, spam, scams, impersonation, or illegal activity.</li>
    <li>False teaching, anti-Christian spirituality, or content that fights the
    app's Christian purpose.</li>
  </ul>
  <h2>Moderation</h2>
  <p>Automated checks may reject comments before posting. Users can report content,
  block users/creators, and admins can hide or remove unsafe content.</p>
  <p>Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
""",
        )
    )


@app.get("/biblemaxxing/support", response_class=HTMLResponse)
def support_page() -> HTMLResponse:
    return HTMLResponse(
        public_page_document(
            "Support",
            f"""
  <p>Need help with BibleMaxxing, account deletion, privacy, reports, moderation,
  or a YouTube source issue?</p>
  <h2>Contact</h2>
  <p>Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
  <h2>Helpful Details</h2>
  <p>When reporting a bug or moderation concern, include your account email, the
  video/comment involved, what happened, and screenshots if useful. Do not send
  passwords or private tokens.</p>
""",
        )
    )


@app.get("/biblemaxxing/player/{youtube_video_id}", response_class=HTMLResponse)
def youtube_player_page(
    youtube_video_id: str, autoplay: bool = Query(default=False)
) -> HTMLResponse:
    if YOUTUBE_VIDEO_ID_PATTERN.fullmatch(youtube_video_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid YouTube video ID"
        )

    return HTMLResponse(
        content=youtube_player_document(youtube_video_id, autoplay),
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Content-Type-Options": "nosniff",
        },
    )


def youtube_player_document(youtube_video_id: str, autoplay: bool) -> str:
    video_id = json.dumps(youtube_video_id)
    watch_url = json.dumps(f"https://www.youtube.com/watch?v={youtube_video_id}")
    autoplay_js = "true" if autoplay else "false"

    return (
        """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover"
  >
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <style>
    html, body, #player {
      background: #000;
      height: 100%;
      margin: 0;
      overflow: hidden;
      width: 100%;
    }

    body {
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    iframe {
      pointer-events: none;
    }

    #fallback {
      align-items: center;
      background: #000;
      box-sizing: border-box;
      display: none;
      inset: 0;
      justify-content: center;
      padding: 28px;
      position: fixed;
      text-align: center;
    }

    #fallback.visible {
      display: flex;
    }

    .title {
      font-size: 18px;
      font-weight: 800;
      margin-bottom: 8px;
    }

    .body {
      color: rgba(255, 255, 255, 0.72);
      font-size: 14px;
      line-height: 1.38;
      margin-bottom: 16px;
      max-width: 280px;
    }

    a {
      color: #fff;
      font-size: 14px;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div id="player"></div>
  <div id="fallback" role="status" aria-live="polite">
    <div>
      <div class="title">Video unavailable</div>
      <div class="body" id="fallback-message">
        This YouTube video cannot be played here. Swipe for another video.
      </div>
      <a id="source-link" rel="noopener">Open on YouTube</a>
    </div>
  </div>

  <script>
    "use strict";

    const videoID = __VIDEO_ID__;
    const watchURL = __WATCH_URL__;
    const shouldAutoplay = __AUTOPLAY__;
    const fallback = document.getElementById("fallback");
    const fallbackMessage = document.getElementById("fallback-message");
    const sourceLink = document.getElementById("source-link");
    sourceLink.href = watchURL;

    let player = null;
    let pendingPlay = false;
    const loopPollIntervalMs = 500;
    const loopNearEndThresholdSeconds = 0.35;

    function post(type, payload) {
      const message = Object.assign({
        type: type,
        videoID: videoID,
        origin: window.location.origin,
        href: window.location.href
      }, payload || {});

      console.log("[BibleMaxxingPlayer]", JSON.stringify(message));

      if (
        window.webkit &&
        window.webkit.messageHandlers &&
        window.webkit.messageHandlers.bibleMaxxingPlayer
      ) {
        window.webkit.messageHandlers.bibleMaxxingPlayer.postMessage(message);
      }
    }

    window.addEventListener("error", function(event) {
      post("window_error", {
        message: event.message,
        source: event.filename,
        line: event.lineno
      });
    });

    window.addEventListener("unhandledrejection", function(event) {
      post("promise_rejection", { message: String(event.reason) });
    });

    function showUnavailable(message) {
      fallbackMessage.textContent = message;
      fallback.classList.add("visible");
      post("unavailable", { message: message });
    }

    function onYouTubeIframeAPIReady() {
      post("iframe_api_ready");

      player = new YT.Player("player", {
        height: "100%",
        width: "100%",
        videoId: videoID,
        playerVars: {
          autoplay: shouldAutoplay ? 1 : 0,
          controls: 0,
          enablejsapi: 1,
          fs: 0,
          iv_load_policy: 3,
          loop: 1,
          modestbranding: 1,
          origin: window.location.origin,
          playlist: videoID,
          playsinline: 1,
          rel: 0,
          widget_referrer: window.location.href
        },
        events: {
          onReady: onPlayerReady,
          onStateChange: onPlayerStateChange,
          onError: onPlayerError,
          onAutoplayBlocked: onAutoplayBlocked
        }
      });
    }

    function onPlayerReady(event) {
      post("player_ready");
      if (shouldAutoplay || pendingPlay) {
        event.target.unMute();
        event.target.playVideo();
        pendingPlay = false;
      }
    }

    function onPlayerStateChange(event) {
      post("player_state", { state: event.data });
      if (event.data === YT.PlayerState.ENDED || event.data === 0) {
        replayCurrentVideo(event.target, "ended_state");
      }
    }

    function replayCurrentVideo(target, reason) {
      post("loop", { name: "replayCurrentVideo", reason: reason });
      target.seekTo(0, true);
      target.playVideo();
    }

    window.setInterval(function() {
      if (!player || !player.getCurrentTime || !player.getDuration) {
        return;
      }
      const duration = Number(player.getDuration() || 0);
      const currentTime = Number(player.getCurrentTime() || 0);
      if (
        duration > 1 &&
        currentTime > 0 &&
        duration - currentTime <= loopNearEndThresholdSeconds
      ) {
        replayCurrentVideo(player, "near_end_poll");
      }
    }, loopPollIntervalMs);

    function onAutoplayBlocked() {
      post("autoplay_blocked");
    }

    function onPlayerError(event) {
      const code = event && typeof event.data !== "undefined" ? String(event.data) : "unknown";
      const messages = {
        "2": "This YouTube video ID is invalid.",
        "5": "This video cannot be played in this embedded player.",
        "100": "This video is private, deleted, or unavailable.",
        "101": "This video owner does not allow embedded playback.",
        "150": "This video owner does not allow embedded playback."
      };
      const message = messages[code] || "This YouTube video cannot be played here.";
      post("player_error", { code: code, message: message });
      showUnavailable(message);
    }

    function playVideo() {
      pendingPlay = true;
      if (player && player.playVideo) {
        player.unMute();
        player.playVideo();
        pendingPlay = false;
        post("command", { name: "playVideo" });
      } else {
        post("command_queued", { name: "playVideo" });
      }
    }

    function pauseVideo() {
      pendingPlay = false;
      if (player && player.pauseVideo) {
        player.pauseVideo();
        post("command", { name: "pauseVideo" });
      }
    }
  </script>
  <script src="https://www.youtube.com/iframe_api"></script>
</body>
</html>
""".replace("__VIDEO_ID__", video_id)
        .replace("__WATCH_URL__", watch_url)
        .replace("__AUTOPLAY__", autoplay_js)
    )


@app.post(f"{API_PREFIX}/auth/register", response_model=schemas.AuthResponse)
def register(
    payload: schemas.RegisterRequest, db: Session = Depends(get_db)
) -> schemas.AuthResponse:
    existing = db.scalar(
        select(models.User).where(
            (models.User.email == payload.email.lower())
            | (models.User.username == payload.username)
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    active_user_count = (
        db.scalar(select(func.count(models.User.id)).where(models.User.deleted_at.is_(None))) or 0
    )
    user = models.User(
        username=payload.username,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        birthday=payload.birthday,
        is_admin=active_user_count == 0,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        ) from None
    db.refresh(user)
    return issue_auth_response(db, user)


@app.post(f"{API_PREFIX}/auth/login", response_model=schemas.AuthResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.AuthResponse:
    user = db.scalar(select(models.User).where(models.User.email == payload.email.lower()))
    if (
        user is None
        or user.deleted_at is not None
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return issue_auth_response(db, user)


@app.post(f"{API_PREFIX}/auth/apple")
def apple_auth_placeholder() -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Sign in with Apple awaits Apple Developer configuration",
    )


@app.post(f"{API_PREFIX}/auth/logout")
def logout(
    session: models.UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> dict:
    session.revoked_at = datetime.now(UTC)
    db.commit()
    return {"ok": True}


@app.get(f"{API_PREFIX}/me", response_model=schemas.UserPublic)
def me(user: models.User = Depends(get_current_user)) -> models.User:
    return user


@app.delete(f"{API_PREFIX}/me")
def delete_account(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    anonymize_deleted_account(db, user, datetime.now(UTC))
    db.commit()
    return {"ok": True}


@app.delete(f"{API_PREFIX}/account")
def delete_account_alias(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return delete_account(user=user, db=db)


@app.post(f"{API_PREFIX}/onboarding", response_model=schemas.UserPublic)
def save_onboarding(
    payload: schemas.OnboardingRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    preference = db.scalar(
        select(models.OnboardingPreference).where(models.OnboardingPreference.user_id == user.id)
    )
    if preference is None:
        preference = models.OnboardingPreference(user_id=user.id)
        db.add(preference)
    preference.topics = sorted(set(payload.topics))
    preference.intensity = payload.intensity
    user.onboarding_completed = True
    for topic in preference.topics:
        slug = services.slugify(topic)
        if slug and db.scalar(select(models.Topic).where(models.Topic.slug == slug)) is None:
            db.add(models.Topic(slug=slug, name=topic))
    db.commit()
    db.refresh(user)
    return user


@app.get(f"{API_PREFIX}/feed", response_model=schemas.FeedResponse)
def feed(
    limit: int = Query(default=12, ge=1, le=50),
    exclude_video_ids: list[str] | None = Query(default=None),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FeedResponse:
    videos = services.feed_for_user(db, user, limit, set(exclude_video_ids or []))
    items: list[schemas.FeedItem] = []
    if services.should_insert_reflection(db, user):
        items.append(
            schemas.FeedItem(
                type="reflection",
                reflection=services.create_reflection_card(db, user, "ten_minute_or_binge_check"),
                rank_reason="A short pause after sustained scrolling.",
            )
        )
    for video in videos:
        items.append(
            schemas.FeedItem(
                type="video",
                video=schemas.VideoPublic.model_validate(video),
                rank_reason="Christ-centered score, theology safety, freshness, and your topics.",
            )
        )
    return schemas.FeedResponse(items=items)


@app.post(f"{API_PREFIX}/feed/impressions")
def record_impression(
    payload: schemas.ImpressionRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_video(db, payload.video_id)
    db.add(
        models.FeedImpression(user_id=user.id, video_id=payload.video_id, position=payload.position)
    )
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/videos/{{video_id}}/watch")
def record_watch(
    video_id: str,
    payload: schemas.WatchEventRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_video(db, video_id)
    db.add(
        models.WatchEvent(
            user_id=user.id,
            video_id=video_id,
            seconds_watched=int(payload.seconds_watched),
            percent_complete=payload.percent_complete,
            rewatched=payload.rewatched,
            event_type=payload.event_type,
        )
    )
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/watch-events")
def record_watch_event_alias(
    payload: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    video_id = payload.get("video_id") or payload.get("videoID")
    if not video_id:
        return {"ok": True, "recorded": False}

    seconds = int(payload.get("seconds_watched") or payload.get("positionSeconds") or 0)
    duration = float(payload.get("durationSeconds") or 0)
    percent_complete = float(payload.get("percent_complete") or 0)
    if not percent_complete and duration > 0:
        percent_complete = max(0, min(1, seconds / duration))

    db.add(
        models.WatchEvent(
            user_id=user.id,
            video_id=video_id,
            seconds_watched=seconds,
            percent_complete=percent_complete,
            rewatched=bool(payload.get("rewatched", False)),
            event_type=payload.get("event_type") or payload.get("eventType") or "progress",
        )
    )
    db.commit()
    return {"ok": True, "recorded": True}


def upsert_unique(db: Session, model: type, **values) -> dict:
    db.add(model(**values))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"ok": True}


def require_video(db: Session, video_id: str) -> models.Video:
    video = db.get(models.Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@app.post(f"{API_PREFIX}/videos/{{video_id}}/like")
def like_video(
    video_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    require_video(db, video_id)
    return upsert_unique(db, models.Like, user_id=user.id, video_id=video_id)


@app.delete(f"{API_PREFIX}/videos/{{video_id}}/like")
def unlike_video(
    video_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Like).filter_by(user_id=user.id, video_id=video_id).delete()
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/videos/{{video_id}}/save")
def save_video(
    video_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    require_video(db, video_id)
    return upsert_unique(db, models.Save, user_id=user.id, video_id=video_id)


@app.delete(f"{API_PREFIX}/videos/{{video_id}}/save")
def unsave_video(
    video_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Save).filter_by(user_id=user.id, video_id=video_id).delete()
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/videos/{{video_id}}/not-interested")
def not_interested(
    video_id: str,
    payload: schemas.NotInterestedRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_video(db, video_id)
    return upsert_unique(
        db, models.NotInterested, user_id=user.id, video_id=video_id, reason=payload.reason
    )


@app.get(f"{API_PREFIX}/videos/{{video_id}}/comments", response_model=list[schemas.CommentPublic])
def comments(
    video_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.Comment]:
    blocked_user_ids = select(models.Block.target_id).where(
        (models.Block.user_id == user.id) & (models.Block.target_type == "user")
    )
    return list(
        db.scalars(
            select(models.Comment)
            .where(
                models.Comment.video_id == video_id,
                models.Comment.moderation_status == "visible",
                models.Comment.user_id.not_in(blocked_user_ids),
            )
            .order_by(models.Comment.created_at.desc())
            .limit(100)
        )
    )


@app.post(f"{API_PREFIX}/videos/{{video_id}}/comments", response_model=schemas.CommentPublic)
def create_comment(
    video_id: str,
    payload: schemas.CommentCreateRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Comment:
    require_video(db, video_id)
    body = payload.body.strip()
    violation = services.comment_policy_violation(body)
    if violation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment violates BibleMaxxing community guidelines.",
        )
    comment = models.Comment(user_id=user.id, video_id=video_id, body=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.post(f"{API_PREFIX}/videos/{{video_id}}/report", response_model=schemas.ReportPublic)
def report_video(
    video_id: str,
    payload: schemas.ReportRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.ModerationReport:
    require_video(db, video_id)
    return services.report_target(db, user.id, "video", video_id, payload.reason, payload.details)


@app.post(f"{API_PREFIX}/comments/{{comment_id}}/report", response_model=schemas.ReportPublic)
def report_comment(
    comment_id: str,
    payload: schemas.ReportRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.ModerationReport:
    if db.get(models.Comment, comment_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return services.report_target(
        db, user.id, "comment", comment_id, payload.reason, payload.details
    )


@app.post(f"{API_PREFIX}/creators/{{creator_id}}/follow")
def follow_creator(
    creator_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return upsert_unique(
        db, models.Follow, user_id=user.id, target_type="creator", target_id=creator_id
    )


@app.delete(f"{API_PREFIX}/creators/{{creator_id}}/follow")
def unfollow_creator(
    creator_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Follow).filter_by(
        user_id=user.id, target_type="creator", target_id=creator_id
    ).delete()
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/topics/{{topic_slug}}/follow")
def follow_topic(
    topic_slug: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return upsert_unique(
        db, models.Follow, user_id=user.id, target_type="topic", target_id=topic_slug
    )


@app.delete(f"{API_PREFIX}/topics/{{topic_slug}}/follow")
def unfollow_topic(
    topic_slug: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Follow).filter_by(
        user_id=user.id, target_type="topic", target_id=topic_slug
    ).delete()
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/creators/{{creator_id}}/block")
def block_creator(
    creator_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return upsert_unique(
        db, models.Block, user_id=user.id, target_type="creator", target_id=creator_id
    )


@app.delete(f"{API_PREFIX}/creators/{{creator_id}}/block")
def unblock_creator(
    creator_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Block).filter_by(
        user_id=user.id, target_type="creator", target_id=creator_id
    ).delete()
    db.commit()
    return {"ok": True}


@app.post(f"{API_PREFIX}/users/{{user_id}}/block")
def block_user(
    user_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    if user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return upsert_unique(db, models.Block, user_id=user.id, target_type="user", target_id=user_id)


@app.delete(f"{API_PREFIX}/users/{{user_id}}/block")
def unblock_user(
    user_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(models.Block).filter_by(
        user_id=user.id, target_type="user", target_id=user_id
    ).delete()
    db.commit()
    return {"ok": True}


@app.get(f"{API_PREFIX}/creators", response_model=list[schemas.CreatorPublic])
def creators(
    query: str | None = None,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.Creator]:
    stmt = select(models.Creator).order_by(models.Creator.display_name)
    if query:
        like_query = f"%{query}%"
        stmt = stmt.where(
            (models.Creator.display_name.ilike(like_query))
            | (models.Creator.handle.ilike(like_query))
        )
    return list(db.scalars(stmt.limit(50)))


@app.get(f"{API_PREFIX}/creators/{{creator_id}}", response_model=schemas.CreatorPublic)
def creator(
    creator_id: str,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Creator:
    creator_row = db.get(models.Creator, creator_id)
    if creator_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator not found")
    return creator_row


@app.get(f"{API_PREFIX}/search", response_model=schemas.SearchResponse)
def search(q: str = Query(min_length=1), db: Session = Depends(get_db)) -> schemas.SearchResponse:
    creators, videos, topics = services.search(db, q)
    return schemas.SearchResponse(creators=creators, videos=videos, topics=topics)


@app.get(f"{API_PREFIX}/reflection/next", response_model=schemas.ReflectionCard)
def reflection(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.ReflectionCard:
    return services.create_reflection_card(db, user, "manual_request")


@app.post(f"{API_PREFIX}/admin/ingest/candidates", response_model=schemas.IngestResponse)
def ingest_candidates(
    payload: schemas.IngestRequest,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.IngestResponse:
    created, skipped = services.upsert_youtube_candidates(
        db, payload.candidates, default_approve=payload.default_approve
    )
    return schemas.IngestResponse(created=created, skipped=skipped)


@app.post(f"{API_PREFIX}/admin/ingest/sample", response_model=schemas.IngestResponse)
def ingest_sample(
    _: models.User = Depends(require_admin), db: Session = Depends(get_db)
) -> schemas.IngestResponse:
    created, skipped = services.seed_sample_inventory(db)
    return schemas.IngestResponse(created=created, skipped=skipped)


@app.get(f"{API_PREFIX}/admin/evals/recommendations")
def admin_recommendation_eval(
    user_id: str | None = None,
    user_email: str | None = Query(default=None, alias="email"),
    limit: int = Query(default=30, ge=1, le=50),
    save: bool = Query(default=True),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    target_user = admin
    if user_id:
        target_user = db.get(models.User, user_id)
    elif user_email:
        target_user = db.scalar(select(models.User).where(models.User.email == user_email))
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    scorecard = evals.evaluate_recommendations_for_user(db, target_user, limit=limit)
    saved_run = (
        evals.persist_eval_run(
            db,
            scorecard,
            category="recommendation",
            subject_user_id=target_user.id,
            source="admin:recommendations",
        )
        if save
        else None
    )
    return evals.eval_scorecard_response(scorecard, saved_run)


@app.post(f"{API_PREFIX}/admin/evals/ingest/candidates")
def admin_ingest_candidate_eval(
    payload: schemas.IngestRequest,
    save: bool = Query(default=True),
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    existing_ids = evals.existing_youtube_ids_for_candidates(db, payload.candidates)
    scorecard = evals.evaluate_ingest_candidates(
        payload.candidates,
        query="admin-candidate-eval",
        existing_youtube_ids=existing_ids,
    )
    saved_run = (
        evals.persist_eval_run(
            db,
            scorecard,
            category="ingestion",
            source="admin:ingest-candidates",
        )
        if save
        else None
    )
    return evals.eval_scorecard_response(scorecard, saved_run)


@app.get(f"{API_PREFIX}/admin/evals/ingest/red-team")
def admin_red_team_ingest_eval(
    save: bool = Query(default=True),
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    scorecard = evals.evaluate_red_team_ingestion()
    saved_run = (
        evals.persist_eval_run(
            db,
            scorecard,
            category="ingestion",
            source="admin:ingest-red-team",
        )
        if save
        else None
    )
    return evals.eval_scorecard_response(scorecard, saved_run)


@app.get(f"{API_PREFIX}/admin/evals/runs", response_model=list[schemas.EvalRunPublic])
def admin_eval_runs(
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.EvalRun]:
    stmt = select(models.EvalRun)
    if category:
        stmt = stmt.where(models.EvalRun.category == category)
    stmt = stmt.order_by(models.EvalRun.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


@app.get(f"{API_PREFIX}/admin/reports", response_model=list[schemas.ReportPublic])
def admin_reports(
    status_filter: str | None = Query(default=None, alias="status"),
    target_type: str | None = Query(default=None, alias="type"),
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.ModerationReport]:
    stmt = select(models.ModerationReport).order_by(models.ModerationReport.created_at.desc())
    if status_filter:
        stmt = stmt.where(models.ModerationReport.status == status_filter)
    if target_type:
        stmt = stmt.where(models.ModerationReport.target_type == target_type)
    return list(db.scalars(stmt.limit(200)))


@app.post(f"{API_PREFIX}/admin/reports/{{report_id}}/resolve")
def admin_resolve_report(
    report_id: str,
    payload: schemas.ReportResolveRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    services.apply_moderation(db, admin, "report", report_id, payload.status, payload.notes)
    return {"ok": True}


@app.get(f"{API_PREFIX}/admin/videos", response_model=list[schemas.VideoPublic])
def admin_videos(
    moderation_status: str | None = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.Video]:
    stmt = select(models.Video).options(joinedload(models.Video.creator))
    if moderation_status:
        stmt = stmt.where(models.Video.moderation_status == moderation_status)
    return list(db.scalars(stmt.limit(200)))


@app.get(f"{API_PREFIX}/admin/comments", response_model=list[schemas.CommentPublic])
def admin_comments(
    moderation_status: str | None = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.Comment]:
    stmt = select(models.Comment).order_by(models.Comment.created_at.desc())
    if moderation_status:
        stmt = stmt.where(models.Comment.moderation_status == moderation_status)
    return list(db.scalars(stmt.limit(200)))


@app.get(f"{API_PREFIX}/admin/users", response_model=list[schemas.UserPublic])
def admin_users(
    query: str | None = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.User]:
    stmt = select(models.User).order_by(models.User.created_at.desc())
    if query:
        like_query = f"%{query}%"
        stmt = stmt.where(
            (models.User.username.ilike(like_query)) | (models.User.email.ilike(like_query))
        )
    return list(db.scalars(stmt.limit(100)))


@app.get(f"{API_PREFIX}/admin/creators", response_model=list[schemas.CreatorPublic])
def admin_creators(
    query: str | None = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[models.Creator]:
    stmt = select(models.Creator).order_by(models.Creator.display_name)
    if query:
        like_query = f"%{query}%"
        stmt = stmt.where(
            (models.Creator.display_name.ilike(like_query))
            | (models.Creator.handle.ilike(like_query))
        )
    return list(db.scalars(stmt.limit(100)))


@app.get(f"{API_PREFIX}/admin/blocks", response_model=list[schemas.BlockPublic])
def admin_blocks(
    _: models.User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[models.Block]:
    return list(
        db.scalars(select(models.Block).order_by(models.Block.created_at.desc()).limit(200))
    )


@app.get(f"{API_PREFIX}/admin/audit-log", response_model=list[schemas.AdminAuditPublic])
def admin_audit_log(
    _: models.User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[models.AdminAudit]:
    return list(
        db.scalars(
            select(models.AdminAudit).order_by(models.AdminAudit.created_at.desc()).limit(200)
        )
    )


@app.patch(f"{API_PREFIX}/admin/{{target_type}}/{{target_id}}")
def admin_moderate(
    target_type: str,
    target_id: str,
    payload: schemas.ModerationUpdateRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    target_type = {
        "videos": "video",
        "comments": "comment",
        "reports": "report",
        "creators": "creator",
        "users": "user",
    }.get(target_type, target_type)
    if target_type not in {"video", "comment", "report", "creator", "user"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported target type"
        )
    services.apply_moderation(db, admin, target_type, target_id, payload.status, payload.notes)
    return {"ok": True}


@app.patch(f"{API_PREFIX}/admin/videos/{{video_id}}/moderation")
def admin_video_moderation_alias(
    video_id: str,
    payload: schemas.ModerationUpdateRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    services.apply_moderation(db, admin, "video", video_id, payload.status, payload.notes)
    return {"ok": True}


@app.patch(f"{API_PREFIX}/admin/comments/{{comment_id}}/moderation")
def admin_comment_moderation_alias(
    comment_id: str,
    payload: schemas.ModerationUpdateRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    services.apply_moderation(db, admin, "comment", comment_id, payload.status, payload.notes)
    return {"ok": True}


@app.patch(f"{API_PREFIX}/admin/users/{{user_id}}")
def admin_user_moderation_alias(
    user_id: str,
    payload: schemas.ModerationUpdateRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    services.apply_moderation(db, admin, "user", user_id, payload.status, payload.notes)
    return {"ok": True}


@app.patch(f"{API_PREFIX}/admin/creators/{{creator_id}}")
def admin_creator_moderation_alias(
    creator_id: str,
    payload: schemas.ModerationUpdateRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    services.apply_moderation(db, admin, "creator", creator_id, payload.status, payload.notes)
    return {"ok": True}
