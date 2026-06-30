# Pre-Submit Completion Audit

Reviewed: 2026-06-30

This is the current evidence-backed audit for the active pre-submit goal. It
separates completed implementation work from items that require Ryan, the
publisher, or Apple's App Store Connect UI.

## Current Verdict

BibleMaxxing is ready for friend-publisher handoff as a source package and local
archiveable iOS project, with a live production backend and verified feed
append behavior.

The remaining App Store submission work is external/manual:

- The friend's Apple Developer team must sign and upload the app.
- App Store Connect metadata, age rating, privacy answers, screenshots, review
  notes, and the private demo-account password must be entered by a human.
- Ryan's physical iPhone needs the latest build reinstalled once `devicectl`
  reports it as available again.

## Requirement Audit

| Requirement | Status | Current Evidence |
| --- | --- | --- |
| Clean GitHub handoff | Done | `master` is the handoff branch; verify with `git status --short` and `git log --oneline -1` before sending. |
| Friend source handoff | Done | Generate from current `HEAD` with `git archive --format=zip HEAD -o /tmp/BibleMaxxing-friend-handoff-$(git rev-parse --short HEAD).zip`. |
| Local archiveability | Done | `/tmp/BibleMaxxingArchive/BibleMaxxing.xcarchive`, bundle id `com.ryanamiri.biblemaxxing`, signing identity `Apple Development: ryankamiri@icloud.com (LWASV7VRQ6)`. |
| App Store distribution upload | External | Requires friend's Apple Developer team, app id, certificates/profiles, and App Store Connect access. |
| Public backend health | Done | `https://api.tailortom.org/biblemaxxing/health` returned `{"ok":true,"service":"biblemaxxing","env":"production"}`. |
| Public legal/support pages | Done | `/privacy`, `/terms`, `/community`, and `/support` each returned HTTP `200`. |
| Production seeded feed | Done | Production counts at audit: `396` videos, `393` approved embeddable videos, `0` open reports, `8` active users, `17` comments. |
| App Review demo account | Done | `ryanamiri05+appreview@gmail.com` login returned HTTP `200`, is non-admin, onboarding is complete, and `/feed?limit=8` returned `8` video items. Do not commit or publish its password outside App Store Connect review notes. |
| Infinite-scroll API exclusion | Done | `python3 scripts/verify_infinite_scroll.py --base-url https://api.tailortom.org/biblemaxxing` returned page 1 `5`, page 2 `8`, and `duplicates: []`. |
| Infinite-scroll tail UX | Done | iOS feed has a full-page loading/caught-up/retry tail state and per-session impression/start de-duping in `ios/BibleMaxxingApp/Features/FeedView.swift`. |
| Current phone install | Manual | `devicectl` currently lists Ryan's iPhone 17 Pro Max as `unavailable`; reinstall when available. Simulator build/install/launch and Release archive have passed. |
| Secret scan | Done | Secret scan only matched placeholder/example variables in `.env.example`, compose examples, dev script, and the QA checklist command itself. |
| YouTube no-download scan | Done | Download scan only matched documentation checklist references. No code path for YouTube audiovisual download/rehost was found. |
| Sign in with Apple | Intentionally hidden | Code path exists for later, but the current review build hides the button because Apple credential exchange is not configured and no third-party/social login is visible. |
| App Store metadata package | Done | Paste-ready metadata, privacy nutrition posture, age-rating guidance, screenshots, and review notes live in `docs/app-store-connect-pre-submit.md` and `docs/app-review-submission.md`. |
| Publisher handoff docs | Done | Friend publishing steps, ownership caveats, guardrails, and final checks live in `docs/app-store-friend-publishing.md`. |

## Latest Verification Commands

```bash
git status --short
git log --oneline -1
git archive --format=zip HEAD -o /tmp/BibleMaxxing-friend-handoff-$(git rev-parse --short HEAD).zip
python3 scripts/verify_infinite_scroll.py --base-url https://api.tailortom.org/biblemaxxing
curl -fsS https://api.tailortom.org/biblemaxxing/health
curl -fsS -o /tmp/bmx-privacy.html -w 'privacy %{http_code}\n' https://api.tailortom.org/biblemaxxing/privacy
curl -fsS -o /tmp/bmx-terms.html -w 'terms %{http_code}\n' https://api.tailortom.org/biblemaxxing/terms
curl -fsS -o /tmp/bmx-community.html -w 'community %{http_code}\n' https://api.tailortom.org/biblemaxxing/community
curl -fsS -o /tmp/bmx-support.html -w 'support %{http_code}\n' https://api.tailortom.org/biblemaxxing/support
rg -n "SECRET|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH|YOUTUBE_API_KEY=.*[A-Za-z0-9_-]{20}|JWT_SECRET|PASSWORD=" .
rg -n "yt-dlp|youtube-dl|ffmpeg|mp4|m3u8|AVAssetDownload|download.*youtube" .
xcrun devicectl list devices
```

## Primary Policy References

- Apple App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Apple app privacy details: https://developer.apple.com/app-store/app-privacy-details/
- Apple account deletion requirement: https://developer.apple.com/support/offering-account-deletion-in-your-app/
- Apple build upload help: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- YouTube API Services Terms: https://developers.google.com/youtube/terms/api-services-terms-of-service
- YouTube Developer Policies: https://developers.google.com/youtube/terms/developer-policies
