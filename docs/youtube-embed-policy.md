# YouTube Embed-Only Content Policy

Reviewed: 2026-06-30

BibleMaxxing v1 uses YouTube as a metadata and embedded-playback source only.
It must not become a downloader, transcoder, cache, or shadow video host.

## Primary Sources

- YouTube API Services Terms of Service: https://developers.google.com/youtube/terms/api-services-terms-of-service
- YouTube API Services Developer Policies: https://developers.google.com/youtube/terms/developer-policies
- YouTube IFrame Player API: https://developers.google.com/youtube/iframe_api_reference
- YouTube embedded player parameters: https://developers.google.com/youtube/player_parameters
- YouTube Data API `videos.list`: https://developers.google.com/youtube/v3/docs/videos/list
- YouTube Data API `search.list`: https://developers.google.com/youtube/v3/docs/search/list
- YouTube Data API quota costs:
  https://developers.google.com/youtube/v3/determine_quota_cost

## Allowed In V1

- Discover candidate videos with official YouTube APIs.
- Store metadata:
  - `youtube_video_id`
  - title
  - description
  - channel ID/title
  - thumbnails
  - duration
  - tags/topics
  - source URLs
  - embeddable/public/availability status
  - moderation status
  - topic/theology scores
  - ranking features and local embeddings
- Play videos through the official embedded player.
- Prefetch metadata, thumbnails, feed candidates, ranking results, and the next
  player shell.
- Cue the next video player so swiping feels fast, as long as audiovisual
  content is still served by the official player.
- Show subtle but accessible source attribution.

## Forbidden In V1

- Do not download YouTube videos.
- Do not cache YouTube audiovisual content.
- Do not convert YouTube videos to MP4 or another media format.
- Do not rehost or serve YouTube audiovisual files from BibleMaxxing.
- Do not implement offline playback for YouTube-sourced videos.
- Do not offer save-to-camera-roll for YouTube-sourced videos.
- Do not scrape Instagram, use Instagram cookies/tokens, automate Instagram
  scrolling, download Instagram Reels, or hide Instagram as a source.
- Do not hide, cover, replace, or interfere with official YouTube player UI,
  ads, links, branding, or playback controls in a way that violates YouTube's
  player/API policies.

## App Implementation Guidance

- iOS should use a `WKWebView` or official compatible embedded player flow for
  YouTube playback.
- Use `playsinline=1` where practical so playback stays in the vertical feed
  experience.
- The first video should require user intent: "Tap to Start" with sound. After
  that, swipes may auto-play/cue within platform rules and iOS behavior.
- Use a previous/current/next player window, but only preload shell/player state
  and metadata. Do not persist audiovisual bytes.
- If a video becomes unavailable, private, deleted, age-restricted, or
  non-embeddable, remove it from feed eligibility.

## Backend Data Rules

Store source and rights metadata with every video:

```text
youtube_video_id
youtube_channel_id
youtube_channel_title
source_url
embed_url
thumbnail_url
duration_seconds
published_at
last_source_refresh_at
is_embeddable
availability_status
moderation_status
attribution_text
```

The ingestion worker should refresh source metadata periodically and treat stale
or unavailable source status as a feed exclusion until revalidated.

## Quota Notes

The YouTube Data API is financially free for the current ingestion worker, but
it is quota-limited. `search.list` calls cost 100 quota units each under
YouTube's quota table, so a 10-query cycle every 2 hours can exceed the default
daily quota unless the project has more quota approved or the query set is
reduced.

## User-Facing Attribution

Every feed video should have an accessible source affordance:

- Channel title.
- "Watch on YouTube" or equivalent source link.
- A report action for "source unavailable", "not Christian", "unsafe theology",
  "harmful/abusive", "sexual", "violent", "spam", and "other".

## QA Checks

- Search the repo for accidental download code:

  ```bash
  rg -n "yt-dlp|youtube-dl|download|mp4|m3u8|ffmpeg|AVAssetDownload|URLSession.*youtube" .
  ```

- Confirm feed items provide `youtube_video_id`, `embed_url`, `source_url`, and
  attribution fields.
- Confirm saved videos are bookmarks only.
- Confirm airplane-mode/offline playback does not work for YouTube-sourced
  videos.
