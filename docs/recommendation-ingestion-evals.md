# Recommendation And Ingestion Evals

This document defines the v1 BibleMaxxing eval system for recommendation quality
and YouTube ingestion quality.

## Why This Shape

Recommendation evals should not stop at one ranking metric. RecList argues that
real recommender behavior needs deployment-specific behavioral tests beyond
held-out ranking scores: https://arxiv.org/abs/2111.09963.

For BibleMaxxing, the important behaviors are:

- Christ-centered and theologically safe inventory.
- Personalized ranking from explicit and passive signals.
- No recycled already-seen feed items.
- Creator, topic, and preacher/source diversity.
- Trusted influencer boosts without one pastor or repost lane dominating.
- Anti-addiction posture, including reflection-card behavior.

YouTube ingestion evals must also account for platform constraints. The worker
uses `search.list` filters such as `videoDuration`, `videoEmbeddable`,
`safeSearch`, and `order`, then validates video `contentDetails` and `status`
through `videos.list`:

- https://developers.google.com/youtube/v3/docs/search/list
- https://developers.google.com/youtube/v3/docs/videos/list
- https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits

## Scorecards

The implementation lives in `backend/app/evals.py`.

Each admin-triggered eval run is also persisted in the backend database in
`eval_runs`. Stored history includes the scorecard name, category, status,
overall score, metrics JSON, gates JSON, notes JSON, optional subject user,
source, and creation timestamp.

### Recommendation Feed

`evaluate_recommendations_for_user(db, user, limit)` calls the real
`services.feed_for_user` recommender, then scores the returned list.

Core metrics:

- feed count versus requested limit
- average spiritual score
- average theology score
- average reel-fit score
- creator coverage
- topic coverage
- max creator share
- max aligned preacher/source share
- trusted influencer share
- consecutive creator/source repeats

Hard gates:

- enough inventory exists
- theology floor does not drop below `0.5`
- no creator dominates more than `35%` of the feed
- no aligned preacher/source dominates more than `35%` of the feed
- no back-to-back aligned source repeats

Fresh app feeds of 12 or fewer videos use a stricter source/person cap in the
reranker so one aligned preacher, such as Philip Anthony Mitchell clips
reposted across many channels, cannot crowd the first screen.

### YouTube Ingestion Candidates

`evaluate_ingest_candidates(candidates, query, existing_youtube_ids)` scores a
candidate batch before write.

Core metrics:

- candidate count
- accepted new count
- rejected-by-filter count
- duplicate count
- trusted influencer candidate count
- red-flag candidate count
- red-flag auto-approved count
- unique channel count
- useful new rate
- duplicate share
- average spiritual/theology/reel-fit scores for accepted new candidates

Hard gates:

- batch has candidates
- no red-flag candidate is auto-approved
- at least one new approved candidate appears when the batch is non-empty
- duplicate waste remains under half the batch

### Query Plan

`evaluate_query_plan(settings, queries)` verifies the worker uses both broad
Christian discovery queries and the rotating pastor/source lane while staying
inside configured per-cycle and estimated daily YouTube search-call budgets.

## How To Run

Local backend defaults:

```bash
scripts/run_evals.py --limit 30
```

For Ryan's production-like account when the script can reach the configured DB:

```bash
scripts/run_evals.py --user-email ryanamiri05@gmail.com --limit 30
```

Write a baseline:

```bash
scripts/run_evals.py --user-email ryanamiri05@gmail.com --limit 30 \
  --write-baseline /tmp/biblemaxxing-eval-baseline.json
```

Compare to a baseline:

```bash
scripts/run_evals.py --user-email ryanamiri05@gmail.com --limit 30 \
  --baseline /tmp/biblemaxxing-eval-baseline.json --fail-on-regression
```

The comparison status is:

- `improving` when current score is at least `2.5` points above baseline.
- `baselining` when it remains within `+/-2.5` points.
- `regressing` when it falls at least `2.5` points below baseline.
- `no_baseline` when no previous scorecard exists.

## Admin Endpoints

Admins can run:

- `GET /biblemaxxing/api/v1/admin/evals/recommendations?email=...&limit=30`
- `POST /biblemaxxing/api/v1/admin/evals/ingest/candidates`
- `GET /biblemaxxing/api/v1/admin/evals/ingest/red-team`
- `GET /biblemaxxing/api/v1/admin/evals/runs?limit=50`

Eval execution endpoints save an `eval_runs` row by default and return
`saved=true` plus `saved_run_id`. Pass `save=false` to run a scorecard without
adding history. The recent-runs endpoint is admin-only and can be filtered with
`category=recommendation` or `category=ingestion`.

## Worker Behavior

`backend/app/youtube_worker.py` logs:

- one query-plan eval per default cycle
- one candidate-batch eval per fetched query
- quota-exhausted errors as a cycle-level stop condition, so one exhausted
  YouTube Search Queries day does not produce repeated failed calls

Live YouTube evals remain opt-in through the worker/script path. Default tests
use deterministic fixtures and do not require network or production secrets.
