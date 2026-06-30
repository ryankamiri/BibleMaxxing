# Models Guide

This folder owns Codable request and response types shared by the app.

- Keep names close to the versioned backend contract under `/biblemaxxing/api/v1`.
- Prefer optional fields for backend values that may evolve while the product matures.
- Do not add persistence or network side effects here.
