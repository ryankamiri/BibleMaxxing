# iOS Agent Guide

This folder owns the native BibleMaxxing iOS app.

Read the root `AGENTS.md` before changing anything here.

## Product Direction

- Build with SwiftUI.
- Dark mode only.
- Target modern iPhones, including Ryan's iPhone 17.
- The first screen after auth/onboarding should be the usable feed, not a marketing landing page.
- Make the app feel like a polished vertical short-video experience without copying Instagram branding or exact UI.

## Feed Playback

- Use YouTube embedded playback for v1, loaded through the backend-hosted
  `/biblemaxxing/player/{youtube_video_id}` shell so `WKWebView` has a stable
  HTTPS origin/referrer.
- Do not download, cache, store, or expose YouTube MP4/video bytes.
- Do not implement save-to-camera-roll for YouTube-sourced videos.
- Use Tap to Start with sound, then auto-play subsequent swipes.
- Prefer a previous/current/next player model for fast swiping.
- Prefetch metadata and thumbnails; cue or prepare the next player where allowed.
- Silently skip unavailable or non-embeddable videos.
- Show subtle creator/source attribution and a way to inspect source details.

## Required UX

- Login before feed for the personal prototype.
- Onboarding before first feed.
- Double tap to like.
- In-app save/bookmark.
- Not interested.
- Follow topics and creators.
- Comments with report/moderation affordances.
- Report video/comment.
- Block user/creator.
- Account deletion flow.
- Reflection/Scripture cards after about 10 minutes and when binge-like behavior is detected.

## Engineering Notes

- Keep networking isolated behind service clients.
- Keep auth state, onboarding state, and feed state testable.
- Avoid business logic in views when a view model/service is clearer.
- UI text should be concise and polished.
- Icons should use native SF Symbols where appropriate.
- Avoid hardcoding production secrets or API keys in the app.

## Current Project Layout

- Xcode project: `BibleMaxxing.xcodeproj`.
- Source root: `BibleMaxxingApp/`.
- App routing: `BibleMaxxingApp/App/`.
- API models: `BibleMaxxingApp/Models/APIModels.swift`.
- Networking/session state: `BibleMaxxingApp/Services/`.
- Reusable UI and YouTube embed wrapper: `BibleMaxxingApp/Components/`.
- Feature screens: `BibleMaxxingApp/Features/`.

The app points at `https://api.tailortom.org/biblemaxxing/api/v1` and stores bearer tokens in Keychain. Feed video playback is through the backend-hosted official YouTube iframe player shell in `WKWebView`; do not add MP4 download, offline playback, or save-to-camera-roll behavior.
