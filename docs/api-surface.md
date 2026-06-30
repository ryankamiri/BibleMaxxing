# BibleMaxxing API Surface

Reviewed: 2026-06-30

Public base URL:

- `https://api.tailortom.org/biblemaxxing`

Expected backend routes. Caddy must proxy these paths through without stripping
`/biblemaxxing`:

- Health: `/biblemaxxing/health`
- Versioned API: `/biblemaxxing/api/v1`

Public examples therefore look like:

- `GET https://api.tailortom.org/biblemaxxing/health`
- `GET https://api.tailortom.org/biblemaxxing/api/v1/feed`

## Response Standards

- JSON request and response bodies.
- Authenticated endpoints use `Authorization: Bearer <access_token>`.
- Use stable opaque IDs for user-facing resources.
- Current prototype responses use FastAPI's default `detail` error shape.
- Cursor pagination is a near-term follow-up; the current feed uses `limit`.

## Health And Metadata

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/biblemaxxing/health` | No | Liveness for Caddy, Docker, and uptime checks. |

Health response:

```json
{
  "ok": true,
  "service": "biblemaxxing",
  "env": "production"
}
```

## Auth And Account

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | No | Email/password registration with username, email, password, and optional birthday. |
| `POST` | `/api/v1/auth/login` | No | Email/password login. |
| `POST` | `/api/v1/auth/apple` | No | Placeholder path until Apple Developer configuration exists. |
| `POST` | `/api/v1/auth/logout` | Yes | Revoke current refresh/session token. |
| `GET` | `/api/v1/me` | Yes | Current user profile and onboarding status. |
| `DELETE` | `/api/v1/me` | Yes | Delete account immediately for prototype. |
| `DELETE` | `/api/v1/account` | Yes | Alias used by the current iOS client. |

Register request:

```json
{
  "username": "ryan",
  "email": "ryan@example.com",
  "password": "long-user-password",
  "birthday": "2005-01-01"
}
```

Account deletion response:

```json
{
  "ok": true
}
```

## Onboarding And Topics

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/onboarding` | Yes | Required pre-feed topic preferences and safety confirmations. Accepts `topics` or `topicSlugs`. |
| `POST` | `/api/v1/topics/{topic_slug}/follow` | Yes | Follow a topic. |
| `DELETE` | `/api/v1/topics/{topic_slug}/follow` | Yes | Unfollow a topic. |

Minimum onboarding topics:

- prayer
- anxiety
- discipline
- apologetics
- workplace holiness
- Bible study
- worship
- testimony
- Christian living
- Scripture
- theology
- gospel encouragement

## Feed

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/feed?limit=10` | Yes | Personalized vertical feed candidates. |
| `POST` | `/api/v1/feed/impressions` | Yes | Record cards shown to the user. |
| `POST` | `/api/v1/videos/{video_id}/watch` | Yes | Watch, skip, completion, rewatch, and dwell events. |
| `POST` | `/api/v1/watch-events` | Yes | Compatibility alias used by the iOS client. |

Feed item response:

```json
{
  "items": [
    {
      "id": "feeditem_123",
      "type": "video",
      "reason": "prayer + workplace holiness",
      "video": {
        "id": "vid_123",
        "youtube_video_id": "abc123xyz",
        "title": "Praying before a hard meeting",
        "channel_title": "Example Channel",
        "thumbnail_url": "https://i.ytimg.com/...",
        "source_url": "https://www.youtube.com/watch?v=abc123xyz",
        "embed_url": "https://www.youtube.com/embed/abc123xyz",
        "duration_seconds": 42,
        "moderation_status": "approved"
      }
    },
    {
      "id": "reflection_456",
      "type": "reflection",
      "trigger": "ten_minute_checkpoint",
      "scripture_reference": "Colossians 3:23",
      "prompt": "How can this next work block become worship?"
    }
  ],
  "next_cursor": "cursor_abc"
}
```

Feed rules:

- Do not return videos with moderation status `rejected`, `hidden`, `blocked`,
  `private`, `deleted`, `age_restricted`, or `non_embeddable`.
- Include enough source metadata for in-app attribution.
- Reflection cards should appear after about 10 minutes of scrolling and when
  binge-like behavior is detected.

## Video Interactions

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/videos/{video_id}/like` | Yes | Like a video. |
| `DELETE` | `/api/v1/videos/{video_id}/like` | Yes | Remove like. |
| `POST` | `/api/v1/videos/{video_id}/save` | Yes | Save/bookmark a video in app. |
| `DELETE` | `/api/v1/videos/{video_id}/save` | Yes | Remove save. |
| `POST` | `/api/v1/videos/{video_id}/not-interested` | Yes | Downrank similar content. |
| `POST` | `/api/v1/videos/{video_id}/report` | Yes | Report a video. |

The current backend accepts `POST` for like/save/follow actions and `DELETE` to
remove them. There is no public share endpoint in v1.

## Creators And Search

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/creators?query=` | Yes | Search creators/channels. |
| `GET` | `/api/v1/creators/{creator_id}` | Yes | Creator profile and metadata. |
| `POST` | `/api/v1/creators/{creator_id}/follow` | Yes | Follow creator. |
| `DELETE` | `/api/v1/creators/{creator_id}/follow` | Yes | Unfollow creator. |
| `POST` | `/api/v1/creators/{creator_id}/block` | Yes | Block creator. |
| `DELETE` | `/api/v1/creators/{creator_id}/block` | Yes | Unblock creator. |

## Comments

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/videos/{video_id}/comments` | Yes | Visible comments for a video. |
| `POST` | `/api/v1/videos/{video_id}/comments` | Yes | Create comment, defaulting to moderation review if needed. |
| `POST` | `/api/v1/comments/{comment_id}/report` | Yes | Report comment. |
| `POST` | `/api/v1/users/{user_id}/block` | Yes | Block a user. |
| `DELETE` | `/api/v1/users/{user_id}/block` | Yes | Unblock a user. |

Comment editing and user deletion/tombstoning are follow-ups. Current v1 admin
moderation hides/removes comments through admin moderation endpoints.

## Admin API

Admin routes require an admin role and should audit every state-changing action.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/admin/reports?status=open&type=` | Report queue. |
| `POST` | `/api/v1/admin/reports/{report_id}/resolve` | Resolve report with action and note. |
| `GET` | `/api/v1/admin/videos?status=pending` | Video moderation queue. |
| `PATCH` | `/api/v1/admin/videos/{video_id}/moderation` | Approve, reject, hide, or label video. |
| `GET` | `/api/v1/admin/comments?status=pending` | Comment moderation queue. |
| `PATCH` | `/api/v1/admin/comments/{comment_id}/moderation` | Approve, hide, delete, or warn. |
| `GET` | `/api/v1/admin/users?query=` | User lookup. |
| `PATCH` | `/api/v1/admin/users/{user_id}` | Suspend, reinstate, or annotate user. |
| `GET` | `/api/v1/admin/creators?query=` | Creator/channel lookup. |
| `PATCH` | `/api/v1/admin/creators/{creator_id}` | Override topic, theology, quality, or block status. |
| `GET` | `/api/v1/admin/blocks` | User and creator block visibility. |
| `GET` | `/api/v1/admin/audit-log` | Moderation and admin action audit trail. |

## Ingestion API Or Scripts

Ingestion can be a CLI/script first and API later. It must:

- Use official YouTube Data API metadata.
- Store only metadata, thumbnails, IDs, source URLs, tags, topic scores,
  moderation status, and ranking features.
- Skip unavailable, private, deleted, age-restricted, or non-embeddable videos.
- Never download, cache, convert, rehost, or serve audiovisual content.

Minimum script commands:

```bash
python scripts/fetch_youtube_candidates.py "Christian shorts prayer" --max-results 50 > /tmp/biblemaxxing-candidates.json
curl -fsS -X POST "$BASE_URL/api/v1/admin/ingest/candidates" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/biblemaxxing-candidates.json
curl -fsS "$BASE_URL/api/v1/admin/reports?status=open" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```
