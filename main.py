"""Run the whole pipeline:  python main.py  [--no-details] [--max-pages N] [--delay S]"""
import argparse
import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from processing.cleaning import COLUMNS, clean_book, clean_quote
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.base_scraper import create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
logger = logging.getLogger("main")


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / "scraper.log", mode="w", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def process_source(raw_records, cleaner):
    """Clean -> validate -> deduplicate one source. Returns (final_records, stats)."""
    stats = {"collected": len(raw_records), "cleaning_errors": 0, "cleaned": 0,
             "rejected": 0, "rejected_by_reason": Counter(), "duplicates": 0, "final": 0}
    cleaned = []
    for raw in raw_records:
        try:
            cleaned.append(cleaner(raw))
        except Exception as exc:
            stats["cleaning_errors"] += 1
            logger.warning("Cleaning failed, record dropped: %s", exc)
    stats["cleaned"] = len(cleaned)

    valid = []
    for rec in cleaned:
        problems = validate_record(rec)
        if problems:
            stats["rejected"] += 1
            stats["rejected_by_reason"].update(problems)
            logger.warning("Rejected %r: %s", rec.get("name_or_title"), problems)
        else:
            valid.append(rec)

    unique, dupes = find_duplicates(valid)
    for d in dupes:
        logger.warning("Duplicate removed: %r", d.get("name_or_title"))
    stats["duplicates"] = len(dupes)
    stats["final"] = len(unique)
    stats["rejected_by_reason"] = dict(stats["rejected_by_reason"])
    return unique, stats


def write_csv(records, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def write_summary(summary, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Multi-source scraping pipeline")
    parser.add_argument("--no-details", action="store_true",
                        help="skip book detail pages (category/description stay empty; much faster)")
    parser.add_argument("--max-pages", type=int, default=None, help="limit pages per source (testing)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    args = parser.parse_args()

    setup_logging()
    start = datetime.now(timezone.utc)
    t0 = time.time()
    session = create_session()
    common = dict(session=session, delay=args.delay, max_pages=args.max_pages)
    sources = [
        (BooksScraper(fetch_details=not args.no_details, **common), clean_book),
        (QuotesScraper(**common), clean_quote),
    ]

    all_records, per_source = [], {}
    for scraper, cleaner in sources:
        name = scraper.source_name
        error = None
        try:
            raw = scraper.scrape()
        except Exception as exc:          # one source failing must not stop the other
            logger.exception("Source %s crashed", name)
            raw, error = [], str(exc)
        records, stats = process_source(raw, cleaner)
        stats.update(pages_scraped=scraper.pages_scraped, parse_errors=scraper.parse_errors,
                     failed_urls=scraper.failed_urls, source_error=error)
        per_source[name] = stats
        all_records.extend(records)

    write_csv(all_records, OUTPUT_DIR / "final_dataset.csv")

    reconciles = all(
        s["collected"] - s["cleaning_errors"] - s["rejected"] - s["duplicates"] == s["final"]
        for s in per_source.values())
    end = datetime.now(timezone.utc)
    summary = {
        "per_source": per_source,
        "totals": {k: sum(s[k] for s in per_source.values())
                   for k in ("collected", "cleaned", "rejected", "duplicates", "final")},
        "final_record_count": len(all_records),
        "counts_reconcile": reconciles,
        "note": "rejected_by_reason counts each failed rule; one record can fail several rules.",
        "start_time": start.isoformat(timespec="seconds"),
        "end_time": end.isoformat(timespec="seconds"),
        "duration_seconds": round(time.time() - t0, 1),
    }
    write_summary(summary, OUTPUT_DIR / "summary_report.json")
    logger.info("Finished: %d rows written, reconcile=%s", len(all_records), reconciles)


if __name__ == "__main__":
    main()
