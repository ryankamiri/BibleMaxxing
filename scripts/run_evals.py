#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
ORIGINAL_CWD = Path.cwd()
VENV_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"
if (
    not os.environ.get("VIRTUAL_ENV")
    and VENV_PYTHON.exists()
    and Path(sys.executable).resolve() != VENV_PYTHON.resolve()
):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from sqlalchemy import select  # noqa: E402

from app import evals, models  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.youtube_worker import build_ingest_query_plan  # noqa: E402


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    with path.open() as handle:
        return json.load(handle)


def resolve_cli_path(path: Path | None) -> Path | None:
    if path is None or path.is_absolute():
        return path
    return ORIGINAL_CWD / path


def baseline_scorecard(
    baseline: dict[str, Any] | None,
    key: str,
) -> dict[str, Any] | None:
    if not baseline:
        return None
    return baseline.get("scorecards", {}).get(key)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run BibleMaxxing recommendation and YouTube ingestion eval scorecards."
    )
    parser.add_argument("--user-email", help="User email to evaluate feed personalization for")
    parser.add_argument("--limit", type=int, default=30, help="Recommendation feed size to score")
    parser.add_argument("--baseline", type=Path, help="Existing JSON report to compare against")
    parser.add_argument("--write-baseline", type=Path, help="Write the current report to this path")
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit non-zero if any scorecard regresses or has a failing status",
    )
    args = parser.parse_args()
    args.baseline = resolve_cli_path(args.baseline)
    args.write_baseline = resolve_cli_path(args.write_baseline)

    settings = get_settings()
    baseline = load_json(args.baseline)
    scorecards: dict[str, dict[str, Any]] = {}
    comparisons: dict[str, dict[str, Any]] = {}

    with SessionLocal() as db:
        user = None
        recommendation = None
        if args.user_email:
            user = db.scalar(select(models.User).where(models.User.email == args.user_email))
            if user is None:
                raise SystemExit(f"No user found for {args.user_email}")
            recommendation = evals.evaluate_recommendations_for_user(db, user, limit=args.limit)
        else:
            users = list(db.scalars(select(models.User).order_by(models.User.created_at.asc()).limit(25)))
            for candidate_user in users:
                candidate_scorecard = evals.evaluate_recommendations_for_user(
                    db, candidate_user, limit=args.limit
                )
                if candidate_scorecard.metrics["feed_count"] > 0:
                    user = candidate_user
                    recommendation = candidate_scorecard
                    break

        if recommendation is not None:
            scorecards["recommendation"] = recommendation.to_dict()
            comparisons["recommendation"] = evals.compare_scorecards(
                recommendation,
                baseline_scorecard(baseline, "recommendation"),
            )
        elif not args.user_email:
            comparisons["recommendation"] = {
                "name": "recommendation_feed",
                "status": "skipped_no_evaluable_user",
                "delta": None,
                "current_score": None,
                "baseline_score": None,
            }

    query_plan, _ = build_ingest_query_plan(settings)
    query_plan_eval = evals.evaluate_query_plan(settings, query_plan)
    scorecards["ingest_query_plan"] = query_plan_eval.to_dict()
    comparisons["ingest_query_plan"] = evals.compare_scorecards(
        query_plan_eval,
        baseline_scorecard(baseline, "ingest_query_plan"),
    )

    red_team = evals.evaluate_red_team_ingestion()
    scorecards["ingest_red_team"] = red_team.to_dict()
    comparisons["ingest_red_team"] = evals.compare_scorecards(
        red_team,
        baseline_scorecard(baseline, "ingest_red_team"),
    )

    report = {
        "scorecards": scorecards,
        "comparisons": comparisons,
        "settings": {
            "env": settings.env,
            "youtube_ingest_interval_seconds": settings.youtube_ingest_interval_seconds,
            "youtube_ingest_max_results": settings.youtube_ingest_max_results,
            "youtube_default_approve": settings.youtube_ingest_default_approve,
        },
    }

    print(json.dumps(report, indent=2, sort_keys=True))

    if args.write_baseline:
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.write_baseline.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if args.fail_on_regression:
        bad_statuses = {"regressed", "watch"}
        regression_statuses = {"regressing"}
        has_bad_scorecard = any(card["status"] in bad_statuses for card in scorecards.values())
        has_regression = any(
            comparison["status"] in regression_statuses for comparison in comparisons.values()
        )
        if has_bad_scorecard or has_regression:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
