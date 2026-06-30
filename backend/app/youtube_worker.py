from __future__ import annotations

import argparse
import logging
import time

from app import services
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
    pastor_query_cursor: int = 0,
) -> tuple[list[str], int]:
    if override_queries:
        return override_queries, pastor_query_cursor

    pastor_queries, next_cursor = rotating_query_batch(
        settings.youtube_ingest_pastor_query_list,
        pastor_query_cursor,
        settings.youtube_ingest_pastor_queries_per_cycle,
    )
    return [*settings.youtube_ingest_query_list, *pastor_queries], next_cursor


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
        except YouTubeAPIError:
            logger.exception("YouTube metadata fetch failed", extra={"query": query})
            continue

        with SessionLocal() as db:
            created, skipped = services.upsert_youtube_candidates(
                db,
                candidates,
                default_approve=settings.youtube_ingest_default_approve,
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
    pastor_query_cursor = 0

    while True:
        query_plan, pastor_query_cursor = build_ingest_query_plan(
            settings,
            override_queries=args.query,
            pastor_query_cursor=pastor_query_cursor,
        )
        ingest_once(queries=query_plan, max_results=args.max_results)
        if args.once:
            return 0
        logger.info("sleeping %s seconds before next ingestion cycle", interval)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
