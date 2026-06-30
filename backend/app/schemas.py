from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    birthday: date | None = None
    is_admin: bool = False
    onboarding_completed: bool = False
    suspended_at: datetime | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    birthday: date | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OnboardingRequest(BaseModel):
    topics: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("topics", "topicSlugs", "topic_slugs"),
    )
    intensity: str = "balanced"


class CreatorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    handle: str
    display_name: str
    youtube_channel_id: str | None = None
    avatar_url: str | None = None
    status: str = "approved"


class TopicPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str | None = None


class VideoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    youtube_video_id: str
    title: str
    description: str
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    source_url: str
    embed_url: str
    published_at: datetime | None = None
    tags: list[str]
    topics: list[str]
    spiritual_score: float
    theology_score: float
    entertainment_score: float
    freshness_score: float
    creator: CreatorPublic


class ReflectionCard(BaseModel):
    id: str
    card_type: str
    title: str
    scripture_reference: str | None = None
    body: str
    prompt: str
    trigger: str


class FeedItem(BaseModel):
    type: str = "video"
    video: VideoPublic | None = None
    reflection: ReflectionCard | None = None
    rank_reason: str


class FeedResponse(BaseModel):
    items: list[FeedItem]


class WatchEventRequest(BaseModel):
    seconds_watched: float = Field(
        ge=0, validation_alias=AliasChoices("seconds_watched", "secondsWatched")
    )
    percent_complete: float = Field(
        ge=0, le=1, validation_alias=AliasChoices("percent_complete", "percentComplete")
    )
    rewatched: bool = False
    event_type: str = Field(
        default="progress", validation_alias=AliasChoices("event_type", "eventType")
    )


class ImpressionRequest(BaseModel):
    video_id: str = Field(validation_alias=AliasChoices("video_id", "videoID"))
    position: int = 0


class NotInterestedRequest(BaseModel):
    reason: str | None = None


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    video_id: str
    body: str
    moderation_status: str
    created_at: datetime


class ReportRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=120)
    details: str | None = Field(
        default=None,
        max_length=2000,
        validation_alias=AliasChoices("details", "notes"),
    )


class ReportPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    target_type: str
    target_id: str
    reason: str
    details: str | None = None
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None


class ReportResolveRequest(BaseModel):
    status: str = "actioned"
    notes: str | None = None


class ModerationUpdateRequest(BaseModel):
    status: str
    notes: str | None = None


class SearchResponse(BaseModel):
    creators: list[CreatorPublic]
    videos: list[VideoPublic]
    topics: list[TopicPublic]


class YouTubeCandidate(BaseModel):
    youtube_video_id: str
    title: str
    description: str = ""
    channel_id: str
    channel_title: str
    thumbnail_url: str | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
    tags: list[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    candidates: list[YouTubeCandidate]
    default_approve: bool = True


class IngestResponse(BaseModel):
    created: int
    skipped: int


class BlockPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    target_type: str
    target_id: str
    created_at: datetime


class AdminAuditPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    admin_id: str
    action: str
    target_type: str
    target_id: str
    notes: str | None = None
    created_at: datetime
