from __future__ import annotations

import argparse
import logging
import time

from app import evals, services
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.youtube import YouTubeAPIError, fetch_candidates

logger = logging.getLogger("biblemaxxing.youtube_worker")


def rotating_query_batch(queries: list[str], cursor: int, count: int) -> tuple[list[str], int]:
    if not queries or count <= 0:
        return [], cursor

    batch_size = min(count, len(queries))
    normalized_cursor = cursor % len(queries)
    batch = [queries[(normalized_cursor + offset) % len(queries)] for offset in range(batch_size)]
    return batch, (normalized_cursor + batch_size) % len(queries)


def build_ingest_query_plan(
    settings: Settings,
    override_queries: list[str] | None = None,
    broad_query_cursor: int = 0,
    pastor_query_cursor: int = 0,
) -> tuple[list[str], int, int]:
    if override_queries:
        return override_queries, broad_query_cursor, pastor_query_cursor

    search_budget = max(1, settings.youtube_ingest_search_calls_per_cycle)
    pastor_count = min(
        settings.youtube_ingest_pastor_queries_per_cycle,
        len(settings.youtube_ingest_pastor_query_list),
        search_budget,
    )
    broad_count = min(
        len(settings.youtube_ingest_query_list),
        max(search_budget - pastor_count, 0),
    )
    if (
        settings.youtube_ingest_query_list
        and settings.youtube_ingest_pastor_query_list
        and broad_count == 0
    ):
        broad_count = 1
        pastor_count = max(0, search_budget - 1)

    broad_queries, next_broad_cursor = rotating_query_batch(
        settings.youtube_ingest_query_list,
        broad_query_cursor,
        broad_count,
    )
    pastor_queries, next_cursor = rotating_query_batch(
        settings.youtube_ingest_pastor_query_list,
        pastor_query_cursor,
        pastor_count,
    )
    return [*broad_queries, *pastor_queries], next_broad_cursor, next_cursor


def should_stop_cycle_for_youtube_error(exc: YouTubeAPIError) -> bool:
    message = f"{exc} {exc.body}".lower()
    return exc.status_code in {403, 429} and "quota" in message


def ingest_once(
    queries: list[str] | None = None, max_results: int | None = None
) -> tuple[int, int]:
    settings = get_settings()
    if not settings.youtube_api_key:
        raise RuntimeError("BIBLEMAXXING_YOUTUBE_API_KEY is required for YouTube ingestion")

    query_list = queries or settings.youtube_ingest_query_list
    per_query_limit = max_results or settings.youtube_ingest_max_results
    total_created = 0
    total_skipped = 0

    for query in query_list:
        try:
            candidates = fetch_candidates(settings.youtube_api_key, query, per_query_limit)
        except YouTubeAPIError as exc:
            logger.exception("YouTube metadata fetch failed", extra={"query": query})
            if should_stop_cycle_for_youtube_error(exc):
                logger.warning("stopping ingestion cycle early because YouTube quota is exhausted")
                break
            continue

        with SessionLocal() as db:
            candidate_eval = evals.evaluate_ingest_candidates(
                candidates,
                query=query,
                existing_youtube_ids=evals.existing_youtube_ids_for_candidates(db, candidates),
            )
            created, skipped = services.upsert_youtube_candidates(
                db,
                candidates,
                default_approve=settings.youtube_ingest_default_approve,
            )
            evals.persist_eval_run(
                db,
                candidate_eval,
                category="ingestion",
                source="worker:ingest-candidates",
            )
        total_created += created
        total_skipped += skipped
        logger.info(
            "ingested query=%r candidates=%s created=%s skipped=%s",
            query,
            len(candidates),
            created,
            skipped,
        )
        logger.info(
            "ingest eval query=%r status=%s score=%.1f accepted_new=%s rejected=%s "
            "duplicates=%s trusted=%s red_flag_auto_approved=%s",
            query,
            candidate_eval.status,
            candidate_eval.overall_score,
            candidate_eval.metrics["accepted_new_count"],
            candidate_eval.metrics["rejected_by_filter_count"],
            candidate_eval.metrics["duplicate_count"],
            candidate_eval.metrics["trusted_influencer_candidate_count"],
            candidate_eval.metrics["red_flag_auto_approved_count"],
        )

    logger.info("ingestion cycle complete created=%s skipped=%s", total_created, total_skipped)
    return total_created, total_skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="BibleMaxxing YouTube metadata ingestion worker")
    parser.add_argument("--once", action="store_true", help="Run one ingestion cycle and exit")
    parser.add_argument("--query", action="append", help="Override configured query list")
    parser.add_argument("--max-results", type=int, help="Override per-query max results")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    interval = settings.youtube_ingest_interval_seconds
    broad_query_cursor = 0
    pastor_query_cursor = 0

    while True:
        query_plan, broad_query_cursor, pastor_query_cursor = build_ingest_query_plan(
            settings,
            override_queries=args.query,
            broad_query_cursor=broad_query_cursor,
            pastor_query_cursor=pastor_query_cursor,
        )
        if not args.query:
            query_plan_eval = evals.evaluate_query_plan(settings, query_plan)
            with SessionLocal() as db:
                evals.persist_eval_run(
                    db,
                    query_plan_eval,
                    category="ingestion",
                    source="worker:query-plan",
                )
            logger.info(
                "ingest query-plan eval status=%s score=%.1f broad_queries=%s "
                "pastor_queries=%s duplicates=%s estimated_daily_search_calls=%.1f",
                query_plan_eval.status,
                query_plan_eval.overall_score,
                query_plan_eval.metrics["broad_query_count"],
                query_plan_eval.metrics["pastor_query_count"],
                query_plan_eval.metrics["duplicate_query_count"],
                query_plan_eval.metrics["estimated_daily_search_calls"],
            )
        ingest_once(queries=query_plan, max_results=args.max_results)
        if args.once:
            return 0
        logger.info("sleeping %s seconds before next ingestion cycle", interval)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
