"""
Near-Real-Time Continuous News Ingestion Scheduler for Global News AI - Phase 9

Periodically fetches RSS news feeds, cleans and enriches newly published articles,
persists new rows to MySQL with duplicate skipping, generates 384-d embeddings,
and updates ChromaDB vector store for instant RAG availability.

Supports:
- Configurable polling interval via .env (NEWS_POLL_INTERVAL_MINUTES)
- '--once' argument for single-cycle execution / testing
- Feed health tracking & retry isolation
- Eventual consistency for pending vector embeddings
- Graceful CTRL+C shutdown
"""

import sys
import os
import time
import signal
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime

# Ensure project root in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.feeds import RSS_FEEDS
from src.database import test_connection, get_connection
from src.rss_collector import collect_all_feeds
from src.cleaner import deduplicate_articles
from src.news_processor import process_article
from src.news_repository import (
    insert_many_news,
    get_pending_embedding_articles,
    update_embedding_status,
)
from src.vector_store import add_or_update_articles, count_vectors

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Global shutdown flag
SHUTDOWN_REQUESTED = False


def signal_handler(signum, frame):
    global SHUTDOWN_REQUESTED
    print("\n🛑 [Shutdown] CTRL+C detected. Finishing current task cleanly before exit...")
    SHUTDOWN_REQUESTED = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run_startup_health_check() -> bool:
    """
    Verifies connectivity to MySQL, RSS feeds configuration, and ChromaDB vector store.
    """
    print("\n" + "=" * 80)
    print(" 🌍 GLOBAL NEWS AI — LIVE CONTINUOUS INGESTION (PHASE 9)")
    print("=" * 80)
    print(" Running Startup Health Check...")

    db_ok = test_connection()
    if not db_ok:
        logger.error("[Health Check FAILED] MySQL database is unavailable.")
        return False

    try:
        vec_count = count_vectors()
        logger.info(f"[Health Check OK] ChromaDB Vector Database initialized ({vec_count} indexed vectors).")
    except Exception as err:
        logger.error(f"[Health Check FAILED] ChromaDB Vector Database error: {err}")
        return False

    logger.info(f"[Health Check OK] {len(RSS_FEEDS)} RSS news feeds configured.")
    print(" All dependencies OK! Scheduler starting...\n")
    return True


def execute_ingestion_cycle(cycle_number: int) -> Dict[str, Any]:
    """
    Executes a single news ingestion cycle:
    RSS Fetch -> Processing & Enrichment -> Deduplication -> MySQL -> Embedding -> Vector DB.
    """
    t_start = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 80)
    print(f" 🔄 INGESTION CYCLE #{cycle_number} STARTED AT {timestamp}")
    print("=" * 80)

    # Step 1: Collect Raw Articles from RSS Feeds
    raw_articles = collect_all_feeds(RSS_FEEDS)
    logger.info(f"[Cycle #{cycle_number}] Retrieved {len(raw_articles)} raw RSS articles across {len(RSS_FEEDS)} feeds.")

    if not raw_articles:
        logger.warning(f"[Cycle #{cycle_number}] No articles collected from feeds.")
        return {
            "cycle": cycle_number,
            "raw": 0,
            "new": 0,
            "duplicates": 0,
            "embedded": 0,
            "duration": round(time.time() - t_start, 2),
        }

    # Step 2: Processing & Enrichment
    processed_articles = []
    rejected_count = 0
    for art in raw_articles:
        processed, _ = process_article(art)
        if processed:
            processed_articles.append(processed)
        else:
            rejected_count += 1

    # Step 3: Remove In-Memory Duplicates
    unique_articles = deduplicate_articles(processed_articles)
    logger.info(
        f"[Cycle #{cycle_number}] Valid Enriched: {len(processed_articles)} | Batch Unique: {len(unique_articles)}"
    )

    # Step 4: MySQL Persistence (Insert new articles, skip duplicates)
    db_res = insert_many_news(unique_articles)
    inserted_count = db_res.get("inserted", 0)
    skipped_count = db_res.get("skipped", 0)
    new_articles = db_res.get("new_articles", [])

    logger.info(
        f"[Cycle #{cycle_number}] MySQL Ingestion -> Inserted: {inserted_count} new articles | Skipped: {skipped_count} duplicates."
    )

    # Step 5: Process Pending Embeddings (Eventual Consistency & Auto-Retry)
    pending_articles = get_pending_embedding_articles(limit=200)
    embedded_count = 0

    if pending_articles:
        logger.info(f"[Cycle #{cycle_number}] Found {len(pending_articles)} pending articles needing embeddings.")
        try:
            upserted = add_or_update_articles(pending_articles)
            if upserted > 0:
                article_ids = [str(a["article_id"]) for a in pending_articles if a.get("article_id")]
                update_embedding_status(article_ids, status="completed")
                embedded_count = upserted
                logger.info(f"[Cycle #{cycle_number}] Vector DB successfully updated with {embedded_count} new vector embeddings.")
        except Exception as vec_err:
            logger.error(f"[Cycle #{cycle_number}] Vector DB indexing failed: {vec_err}. Articles remain 'pending' for next retry.")

    duration = round(time.time() - t_start, 2)
    total_vectors = count_vectors()

    # Step 6: Print Cycle Summary Report
    print("\n" + "-" * 80)
    print(f" 📊 INGESTION REPORT (CYCLE #{cycle_number})")
    print("-" * 80)
    print(f" Feeds Monitored       : {len(RSS_FEEDS)}")
    print(f" Raw Articles Fetched  : {len(raw_articles)}")
    print(f" Valid Enriched        : {len(processed_articles)}")
    print(f" MySQL Newly Inserted  : {inserted_count}")
    print(f" Duplicates Skipped    : {skipped_count}")
    print(f" Embeddings Generated  : {embedded_count}")
    print(f" Total Vector DB Size  : {total_vectors} documents")
    print(f" Ingestion Duration    : {duration} seconds")
    print("=" * 80 + "\n")

    return {
        "cycle": cycle_number,
        "raw": len(raw_articles),
        "new": inserted_count,
        "duplicates": skipped_count,
        "embedded": embedded_count,
        "duration": duration,
    }


def start_scheduler(poll_interval_minutes: int = 10, run_once: bool = False):
    """
    Main continuous scheduler loop.
    """
    if not run_startup_health_check():
        print("❌ Ingestion Scheduler cancelled due to health check failures.")
        return

    poll_seconds = max(60, poll_interval_minutes * 60)
    cycle_count = 1

    print(f" ⚙️ Polling Interval: {poll_interval_minutes} minutes ({poll_seconds} seconds)")
    print(" Press CTRL+C to stop continuous ingestion cleanly.\n")

    while not SHUTDOWN_REQUESTED:
        stats = execute_ingestion_cycle(cycle_count)

        if run_once:
            print(" 🏁 Single-cycle (--once) mode requested. Exiting scheduler cleanly.")
            break

        if SHUTDOWN_REQUESTED:
            break

        print(f" 💤 Sleeping {poll_interval_minutes} minutes until next cycle (Cycle #{cycle_count + 1})...")

        # Sleep in small 1-second chunks to respond instantly to CTRL+C
        for _ in range(poll_seconds):
            if SHUTDOWN_REQUESTED:
                break
            time.sleep(1)

        cycle_count += 1

    print("\n👋 Scheduler shut down cleanly. All resources closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global News AI Near-Real-Time Ingestion Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ingestion cycle and exit (useful for testing).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("NEWS_POLL_INTERVAL_MINUTES", "10")),
        help="Polling interval in minutes (default: 10).",
    )

    args = parser.parse_args()
    start_scheduler(poll_interval_minutes=args.interval, run_once=args.once)
