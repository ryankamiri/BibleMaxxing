# BibleMaxxing iOS

Native SwiftUI scaffold for the BibleMaxxing personal prototype.

## Open Or Build

- Open `ios/BibleMaxxing.xcodeproj` in Xcode 26.4 or newer.
- Select the `BibleMaxxing` target and an iPhone simulator.
- CLI simulator build:

```bash
xcodebuild \
  -project ios/BibleMaxxing.xcodeproj \
  -target BibleMaxxing \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

## Backend Contract

The app points at:

```text
https://api.tailortom.org/biblemaxxing/api/v1
```

The API client currently expects these versioned resources:

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/apple`
- `GET /me`
- `DELETE /me`
- `POST /onboarding`
- `GET /feed?limit=12`
- `POST /feed/impressions`
- `POST /videos/{id}/watch`
- `POST|DELETE /videos/{id}/like`
- `POST|DELETE /videos/{id}/save`
- `POST /videos/{id}/not-interested`
- `GET|POST /videos/{id}/comments`
- `POST /videos/{id}/report`
- `POST /comments/{id}/report`
- `POST /creators/{id}/follow`
- `POST /creators/{id}/block`
- `POST /topics/{slug}/follow`
- `GET /search?q=`

The register body uses `{username,email,password,birthday?}`. Onboarding sends `{topics:[String], intensity:String}` and expects a `User` response. Feed items decode `type`, `rank_reason`, the current video score fields, YouTube `embed_url`, and creator fields including `handle`, `display_name`, and `youtube_channel_id`.

## Content Rules Implemented In The App Shell

- YouTube playback uses `WKWebView` with the official iframe player API.
- The app does not download, cache, convert, rehost, or save YouTube audiovisual content.
- Auth is required before onboarding, and onboarding is required before the feed.
- Account tokens are stored in Keychain.
- The feed has Tap to Start, then autoplay state hooks for subsequent swipes.
- The feed keeps previous/current/next player preparation where feasible.
- Like, save, not interested, comment, report, block, creator follow, topic follow, and account deletion UI affordances are scaffolded.

## Current Limitations

- Live auth/feed behavior depends on the deployed FastAPI service being reachable at the configured base URL.
- A local sample feed appears if `GET /feed` fails or returns empty; it is a scaffold fallback and should be replaced by moderated YouTube metadata from the backend.
- Sign in with Apple uses the native code path, but full device use will still require Apple Developer configuration.
