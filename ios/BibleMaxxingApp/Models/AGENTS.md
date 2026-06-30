# Models Guide

This folder owns Codable request and response types shared by the app.

- Keep names close to the versioned backend contract under `/biblemaxxing/api/v1`.
- Prefer optional fields for backend values that may evolve while the product matures.
- Keep admin/eval Codable types flexible enough for evolving scorecard metrics
  and moderation queues.
- Do not add persistence or network side effects here.
