# Services Guide

This folder owns networking, auth session state, and secure token storage.

- The production API base URL is `https://api.tailortom.org/biblemaxxing/api/v1`.
- `APIClient.youtubePlayerPageURL(videoID:autoplay:)` derives the
  `/biblemaxxing/player/{youtube_video_id}` shell URL from the API base URL.
- Do not hardcode API keys, YouTube keys, passwords, cookies, or tokens.
- Keep service methods small and named after backend resources.
- Store bearer tokens in Keychain, not in source files or plain preferences.
