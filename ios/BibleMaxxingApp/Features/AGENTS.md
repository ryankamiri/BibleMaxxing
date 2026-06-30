# Features Guide

This folder owns user-facing SwiftUI screens and feature view models.

- Keep auth, onboarding, feed, comments, reports, and settings flows concise and usable.
- Keep app-facing copy publishable. Do not show prototype, scaffold, API,
  backend, endpoint, or local-token language to users.
- Keep API calls in view models or session services rather than deeply inside view layout.
- Show source attribution and moderation/report/block affordances in the feed.
- Keep privacy, terms, community-guidelines, and support links visible on the
  unauthenticated auth screen and in Settings.
- Settings may expose the mobile admin dashboard only when
  `session.currentUser?.isAdmin == true`; keep admin screens operational and
  queue-focused rather than marketing-oriented.
- No share feature in v1.
