# Multi-Source Web Scraping & Data Consolidation

A Python ETL pipeline that scrapes **Books to Scrape** (1,000 books, 50 pages) and **Quotes to Scrape** (100 quotes, 10 pages), cleans and validates the data, removes duplicates, and writes one CSV, a JSON summary and a log.

```
Scrape -> Clean -> Validate -> Deduplicate -> Consolidate -> Save files
```

## Setup
Python 3.12 (3.10 to 3.12 supported).
```
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Dependencies: `requests`, `beautifulsoup4`, `lxml` (+ `pytest` for tests). Versions are pinned in `requirements.txt`.

## Run
```
python main.py                  # full run (visits every book detail page, about 22 minutes)
python main.py --no-details     # fast run: category/description stay empty
python main.py --max-pages 2    # quick smoke test
python main.py --delay 1.0      # slower / politer
pytest                          # 19 unit tests, no internet needed
```
Outputs: `output/final_dataset.csv`, `output/summary_report.json`, `logs/scraper.log`.

## Result of the final run
1,000 books + 100 quotes = **1,100 rows**; 0 rejected, 0 duplicates, 0 failed URLs; counts reconcile. Timestamps in the summary and CSV are UTC.

## Site observations
| Item | Books to Scrape | Quotes to Scrape |
|---|---|---|
| Record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a` (full title in `title` attribute; visible text is truncated) | `span.text` (curly quotes) |
| Price / Rating | `p.price_color` / class on `p.star-rating` (word) | none |
| Author / Tags | none | `small.author` / `a.tag` |
| Link | `h3 > a[href]` (relative) | `a[href^="/author/"]` |
| Next page | `li.next > a` (relative) | `li.next > a` |
| Category / description | only on detail page (breadcrumb, `#product_description + p`) | none |

## How pagination works
`BaseScraper.scrape()` starts at the home page, parses it, looks for `li.next > a`, converts the relative href to a full URL with `urljoin`, and repeats until no next link exists. No page numbers are hard-coded.

## Data model
Columns (same on every row): `source, source_url, name_or_title, category, price, rating, author, tags, description, scraped_at`.
Non-applicable fields are left empty (never invented, e.g. quotes have no price).

| Column | Books | Quotes |
|---|---|---|
| source_url | book detail page URL | URL of the listing page where the quote appeared |
| name_or_title | full title | quote text without curly quotes |
| category / description | from detail page | empty |
| price / rating | float / int 1-5 | empty |
| author / tags | empty | author / `tag1;tag2` (lowercase, sorted) |
| scraped_at | UTC ISO timestamp | UTC ISO timestamp |

## Cleaning
Pure functions in `processing/cleaning.py`: whitespace and `\xa0` collapse, quote stripping, price to float, rating word to int, tag normalisation, URL normalisation. Pages are decoded as UTF-8 so `£` is not corrupted.

Book descriptions needed extra cleaning (`clean_description`), found by inspecting the real output: the site's HTML contains a truncated copy of the description followed by the full text and a trailing `...more`, and some descriptions contain mis-encoded characters (e.g. `Ã´`). The function removes the truncated copy and the `...more` marker, and repairs the encoding when the fix applies.

## Validation
`validate_record` returns a list of reasons: `unknown_source`, `missing_name`, `invalid_url`, `invalid_price`, `invalid_rating`. Rejected records are logged as warnings and counted by reason in the summary (a record failing several rules counts once as rejected but once per rule in `rejected_by_reason`).

## Deduplication
Fingerprint = SHA-256 of a lowercased, punctuation-stripped, whitespace-collapsed key:
- Books: `source + title + price`
- Quotes: `source + author + first 50 characters of the quote`

Price is part of the book key because the real data contains two different books titled "The Star-Touched Queen" (GBP 46.02 and GBP 32.30). A first version used the title only and wrongly removed one of them. Differences in case, spacing and punctuation are still treated as the same record.

The first occurrence is kept and later ones are **removed** (the dataset is meant to be analysis-ready); the count is reported in the summary and each removal is logged. The real sites contain no true duplicates, so the logic is proven by unit tests with deliberately duplicated data.

## Error handling
- Session with timeout and retries (1s/2s/4s backoff) for HTTP 429/500/502/503/504 and dropped connections. During one test run a brief network drop occurred and the retries recovered from it.
- Per-record `try/except` in parsers; missing elements return `None`.
- A page that still fails after retries is logged and stops *that source only*; each source also runs in its own `try/except`.
- A failed book detail page leaves category/description empty; the book is still kept.

## Summary report
Per source: collected, cleaned, rejected (+reasons), duplicates, final, pages scraped, parse errors, failed URLs. Plus totals, start/end time, duration and `counts_reconcile` (raw - cleaning errors - rejected - duplicates = final).

## Assumptions and limitations
- Only the two practice sites are supported; selectors are site-specific.
- Requests are sequential with a 0.5s pause, so the full run takes about 22 minutes by design.
- There is no checkpoint/resume: a re-run starts from the beginning.
- Availability (Books) and author-page details (Quotes) are not collected.
- Book duplicates are judged by title + price, so two different books with the same title and price would be merged.
- Quotes `source_url` is the listing page, so many quotes share one URL.
- Some descriptions contain run-together words (e.g. "RockabyeRockabye") that come from the site's own data and are left unchanged.
- `robots.txt` is not parsed programmatically.

## AI usage
See `AI_USAGE.md`.