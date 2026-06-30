# Friend Publisher Handoff

Reviewed: 2026-06-30

This is the handoff if a friend publishes BibleMaxxing from their Apple
Developer Program account.

## Ownership Reality

- This is possible if the friend has an active Apple Developer Program
  membership.
- There is no extra Apple submission fee per app if their membership is active,
  but their account still pays the Apple Developer Program annual membership fee.
- The App Store listing, seller name, agreements, tax/banking setup, App Review
  messages, TestFlight, and production app ownership live under the friend's
  Apple developer team.
- If Ryan wants to own the listing later, the app would need to be transferred to
  Ryan's own paid Apple Developer Program account.
- If the friend is enrolled as an individual, any added users get App Store
  Connect access only and are not full Apple Developer Program team members.

Apple references:

- https://developer.apple.com/programs/
- https://developer.apple.com/support/compare-memberships/
- https://developer.apple.com/help/app-store-connect/manage-your-team/add-and-edit-users/
- https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- https://developer.apple.com/help/account/access/roles/

## Recommended Handoff

1. Give the friend access to the GitHub repository, or send a clean source
   archive generated from the current `HEAD`, for example:
   `git archive --format=zip HEAD -o /tmp/BibleMaxxing-friend-handoff-$(git rev-parse --short HEAD).zip`.
2. The friend clones the repo and opens `ios/BibleMaxxing.xcodeproj` in Xcode.
3. In Xcode, the friend selects their Apple developer team for signing.
4. Use a production bundle identifier that belongs to the friend's team. If
   changing the bundle ID, update YouTube WebView referer/origin behavior and
   re-test playback.
5. Archive from Xcode and upload to App Store Connect.
6. In App Store Connect, create the app record, fill metadata, add privacy
   answers, upload screenshots, attach the processed build, and submit.

## App Store Connect Values

- Privacy Policy: https://api.tailortom.org/biblemaxxing/privacy
- Terms of Service: https://api.tailortom.org/biblemaxxing/terms
- Community Guidelines: https://api.tailortom.org/biblemaxxing/community
- Support URL: https://api.tailortom.org/biblemaxxing/support
- Contact email: ryanamiri05@gmail.com
- Demo account email: ryanamiri05+appreview@gmail.com
- Demo account password: provide privately in App Store Connect only.

Use the review notes in `docs/app-review-submission.md`.

## Metadata Guardrails

Use language like:

> Christian short-video feed with reflection breaks and Bible-centered curation.

Avoid:

- "Instagram clone"
- "Reels clone"
- "YouTube replacement"
- "Download YouTube videos"
- Hidden or misleading source claims

Do not put Instagram, Reels, or YouTube trademarks in keywords. Mention YouTube
only where truthful source attribution or review-note explanation is required.

## Compliance Guardrails

Keep these intact before submission:

- Official YouTube embedded playback only.
- No YouTube audiovisual download, caching, conversion, rehosting, offline
  playback, or camera-roll save.
- Clear source attribution and "Open on YouTube".
- No more than one player autoplaying at a time.
- YouTube player must remain visible and must not be obscured by UI overlays.
- Public privacy, terms, community-guidelines, and support links accessible
  before login and in Settings.
- Account deletion reachable in Settings.
- Report video, report comment, block creator, and block user reachable.
- Comment profanity/abuse filtering active before comments publish.
- Backend healthy and demo account feed seeded.

Policy references:

- https://developer.apple.com/app-store/review/guidelines/
- https://developers.google.com/youtube/terms/api-services-terms-of-service
- https://developers.google.com/youtube/terms/developer-policies
- https://developers.google.com/youtube/terms/required-minimum-functionality
- https://www.youtube.com/static?template=terms

## Final Pre-Submit Checks

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests
backend/.venv/bin/python -m ruff check backend scripts/run_evals.py
xcodebuild -project ios/BibleMaxxing.xcodeproj \
  -scheme BibleMaxxing \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Verify live:

```bash
curl -fsS https://api.tailortom.org/biblemaxxing/health
curl -fsS https://api.tailortom.org/biblemaxxing/privacy
curl -fsS https://api.tailortom.org/biblemaxxing/terms
curl -fsS https://api.tailortom.org/biblemaxxing/community
curl -fsS https://api.tailortom.org/biblemaxxing/support
```
