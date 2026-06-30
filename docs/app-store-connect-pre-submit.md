# App Store Connect Pre-Submit Package

Reviewed: 2026-06-30

This is the paste-ready App Store Connect package for BibleMaxxing. It is not
legal advice; validate it against the final build, privacy policy, and the
publisher's Apple Developer account before submission.

## Official References

- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- App privacy details: https://developer.apple.com/app-store/app-privacy-details/
- Account deletion requirement: https://developer.apple.com/support/offering-account-deletion-in-your-app/
- Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
- Upload builds: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/

## App Information

- Name: BibleMaxxing
- Subtitle: Christian short-video reflection
- Primary category: Lifestyle
- Secondary category: Education
- Content rights: uses official YouTube embedded playback and YouTube Data API
  metadata; BibleMaxxing does not download, cache, convert, rehost, or claim
  ownership of YouTube audiovisual content.
- Copyright: 2026 Ryan Amiri, or the legal entity/person shown as seller in the
  publisher's App Store Connect account.
- Support URL: https://api.tailortom.org/biblemaxxing/support
- Privacy Policy URL: https://api.tailortom.org/biblemaxxing/privacy
- Terms URL: https://api.tailortom.org/biblemaxxing/terms
- Contact email: ryanamiri05@gmail.com

## Metadata Copy

Promotional text:

```text
Replace distracted scrolling with Christian short videos, reflection breaks, and Bible-centered curation.
```

Description:

```text
BibleMaxxing is a Christian short-video feed built for Scripture-shaped focus instead of distracted scrolling.

Watch short Christian videos, follow trusted topics and creators, save videos inside the app, join moderated comments, and use reflection breaks that help you pause before the feed becomes a habit loop.

The feed is curated around Bible-centered Christian content, theological safety, topic preferences, source diversity, and user feedback such as likes, saves, not-interested signals, and watch behavior. Users can report videos or comments, block users or creators, and delete their account in Settings.
```

Keywords draft, keep under App Store Connect's current 100-character limit:

```text
Christian,Bible,prayer,devotional,Scripture,Jesus,faith,discipleship,worship,sermon
```

Review notes:

```text
BibleMaxxing is a Christian short-form video feed with reflection breaks and Bible-centered curation.

Video playback uses official YouTube embedded playback and YouTube Data API metadata. The app does not download, cache, convert, rehost, or serve YouTube audiovisual content. Saved videos are in-app bookmarks only, and the app does not offer offline playback or save-to-camera-roll for YouTube-sourced videos.

Users can report videos/comments, block users/creators, delete their account in Settings, and contact the app owner at ryanamiri05@gmail.com for moderation, privacy, or support concerns. Comments are filtered for profanity/abuse before posting and can be reported and moderated through the admin workflow.

Sign in with Apple code exists for future configuration, but the current review build exposes only email/password auth because no third-party or social login provider is enabled in the UI.

Demo account:
Email: ryanamiri05+appreview@gmail.com
Password: [provide privately in App Store Connect]
```

## Privacy Nutrition Answers

Tracking:

- Does this app use data to track the user across apps and websites owned by
  other companies? No.
- Does this app use the advertising identifier? No.
- Third-party advertising: No.

Data collected and linked to the user:

- Contact Info, Email Address: used for account creation, login, security,
  support, and account deletion.
- Identifiers, User ID: used for authentication, account state, moderation,
  and personalization.
- User Content, Comments: used for comments, display, reports, and moderation.
- User Content, Other User Content: report details submitted by users, used for
  safety and moderation.
- Usage Data, Product Interaction: feed impressions, watch events, likes, saves,
  follows, not-interested actions, reports, blocks, onboarding topics, and
  reflection events. Used for app functionality, product personalization,
  safety, and internal quality checks.

Data not collected in v1:

- Phone number
- Precise or coarse location
- Contacts
- Photos or videos from the user's library
- Purchases
- Financial info
- Health or fitness info
- Search history, unless a future build stores searches
- Browsing history
- Sensitive info
- Diagnostics collected by BibleMaxxing code, unless a future crash or analytics
  SDK is added

Data deletion:

- Users can delete their account in Settings.
- Current backend behavior revokes sessions, marks the user deleted, anonymizes
  username/email/password hash/birthday/admin state, clears preference and
  interaction rows, tombstones public comments, and clears user-submitted report
  details while preserving moderation structure needed for safety.

## Age Rating Guidance

Recommended posture: 13+.

Use honest final-build answers, but the intended v1 answers are:

- Kids Category: No.
- Made for Kids: No.
- User-generated content: Yes, because comments/profiles exist.
- UGC moderation/report/block controls: Yes.
- Unrestricted web access: No. The app has public legal/support links and
  source attribution links, but no general web browser.
- Gambling, contests, loot boxes, alcohol/tobacco/drugs, medical treatment:
  No.
- Mature/suggestive/sexual/horror/gore content: None expected in approved feed.
- Profanity or crude humor: None expected; comment filtering and reports are
  active.
- Religious content: Christian religious content is the core purpose. Answer
  any App Store Connect religion-related prompt truthfully if shown.

## Screenshots To Upload

Generate at least the required iPhone screenshot sizes in App Store Connect.
The generated iPhone 17 simulator images are `1206 x 2622`, which Apple lists
as an accepted 6.3-inch iPhone portrait screenshot size.
Preferred screenshot set:

- Auth or welcome screen with logo and no private email visible.
- Onboarding topic selection.
- Main feed with clear BibleMaxxing UI and truthful source attribution.
- Comment/report safety surface.
- Settings screen showing Privacy, Terms, Guidelines, Support, and Delete
  account.

Current local candidate folder:

- `docs/app-store-assets/screenshots/`

Current generated iPhone 17 candidates:

- `docs/app-store-assets/screenshots/iphone17-auth-login.png`
- `docs/app-store-assets/screenshots/iphone17-feed-tap-to-start.png`
- `docs/app-store-assets/screenshots/iphone17-comments-empty.png`
- `docs/app-store-assets/screenshots/iphone17-settings-legal.png`

Do not use screenshots that show a demo password, private inbox, terminal,
Simulator chrome, or the user's private email.

## Signing And Upload

Current local project values:

- Bundle ID: `com.ryanamiri.biblemaxxing`
- Marketing version: `0.1.0`
- Build number: `1`
- Current local development team: `WM6CYD3C9R`
- Device family: iPhone only

For Ryan's friend to publish:

1. Add the friend to the GitHub repo or send them a clean archive of the repo.
2. The friend opens `ios/BibleMaxxing.xcodeproj` in Xcode.
3. The friend chooses their paid Apple Developer team in Signing & Capabilities.
4. If their team cannot use `com.ryanamiri.biblemaxxing`, choose a bundle ID
   owned by their team and retest playback/source links.
5. Product > Archive in Xcode.
6. Distribute App > App Store Connect > Upload.
7. Wait for App Store Connect processing, attach the build, fill this package's
   metadata/privacy/age-rating answers, add screenshots, and submit.

Command-line archive shape, after signing is configured:

```bash
xcodebuild -project ios/BibleMaxxing.xcodeproj \
  -scheme BibleMaxxing \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath build/BibleMaxxing.xcarchive \
  archive
```

External blocker: this machine cannot complete App Store distribution signing
under the friend's Apple team until that team is selected in Xcode and valid
certificates/profiles are available.
