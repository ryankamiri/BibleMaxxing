# App Store Compliance Path

Reviewed: 2026-06-30

This is a build checklist, not legal advice. Keep final privacy, terms, and
App Review metadata reviewed before a real submission.

## Primary Sources

- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Offering account deletion in your app: https://developer.apple.com/support/offering-account-deletion-in-your-app/
- Sign in with Apple: https://developer.apple.com/sign-in-with-apple/get-started/
- App privacy details: https://developer.apple.com/app-store/app-privacy-details/

## V1 App Store Posture

BibleMaxxing should be built so it can graduate from personal prototype to
TestFlight and App Store review without rewrites:

- Native SwiftUI app.
- Dark mode only, but still accessible.
- User account required before feed.
- Email/password auth and Sign in with Apple code path.
- No phone collection.
- Declared age or birthday gate supporting a 13+ posture.
- In-app account deletion.
- User-generated comments with moderation, reporting, blocking, and admin review.
- YouTube embedded playback only.
- Clear source attribution.
- Privacy policy and terms drafts in `docs/` before TestFlight/App Store use.

## Guideline Risk Areas

### User-Generated Content

Comments and public profiles require:

- Content filtering before or soon after publication.
- Report buttons for comments, videos, users, and creators.
- Block user/creator flows.
- Admin review with timely action.
- Contact path for users to reach the app owner.
- Audit trail for moderation decisions.

### Account Deletion

The app must offer account deletion inside the app. The backend should support:

- Authenticated `DELETE /api/v1/me`.
- Clear confirmation before deletion.
- Deletion or anonymization of personal data not needed for legal/safety
  obligations.
- Session/token revocation.
- Reasonable handling of public comments, reports, moderation logs, and audit
  trails.

### Sign in with Apple

Keep the Sign in with Apple path ready if the app offers third-party or social
login options. For the personal prototype, backend and iOS can include the code
path even if final Apple Developer configuration is not complete yet.

### Third-Party Video

The app must not imply ownership of YouTube videos. It should:

- Use official embedded playback.
- Preserve attribution and source URLs.
- Skip non-embeddable/unavailable videos.
- Avoid offline playback and camera-roll saves for YouTube-sourced videos.
- Avoid copying Instagram branding or exact UI details.

### Data Minimization And Privacy

Collect only what v1 needs:

- username
- email
- password hash or Apple account identifier
- declared age or birthday
- onboarding topics
- follows
- likes/saves/not-interested
- watch/feed events
- comments/reports/blocks
- moderation/admin audit data

Do not collect phone numbers in v1.

## Required App Surfaces

- Terms and privacy links during registration.
- Account deletion in settings.
- Report video/comment/user/creator.
- Block user/creator.
- Contact/support email or form.
- Public profile visibility expectations.
- Source attribution for videos.
- Empty/error states for unavailable YouTube content.

## App Review Notes Draft

Use this as a starting point when submitting later:

```text
BibleMaxxing is a Christian short-form video feed that uses official YouTube
embedded playback and YouTube Data API metadata. The app does not download,
cache, convert, rehost, or serve YouTube audiovisual content. Users can report
videos/comments, block users/creators, delete their accounts in app, and contact
the app owner for moderation or privacy concerns.
```

## Open Items Before TestFlight/App Store

- Final privacy policy and terms.
- Apple Developer team/app identifier.
- Sign in with Apple service ID/client secret setup.
- Age rating questionnaire.
- Support/contact email.
- Moderation response process and admin login hardening.
- Review of YouTube API Services compliance after real ingestion is live.
