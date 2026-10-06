"""Quotes to Scrape: selectors and pagination."""
import logging
from urllib.parse import urljoin

from .base_scraper import BaseScraper, utc_now

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    source_name = "Quotes to Scrape"
    start_url = "https://quotes.toscrape.com/"

    def parse_page(self, soup, page_url):
        records = []
        for div in soup.select("div.quote"):
            try:
                records.append(self.parse_quote(div, page_url))
            except Exception as exc:
                self.parse_errors += 1
                logger.warning("[Quotes] Skipped a record on %s: %s", page_url, exc)
        return records

    def parse_quote(self, div, page_url):
        text = div.select_one("span.text")
        author = div.select_one("small.author")
        author_link = div.select_one('a[href^="/author/"]')
        return {
            "text": text.get_text() if text else None,
            "author": author.get_text() if author else None,
            "tags": [t.get_text() for t in div.select("a.tag")],
            "author_href": urljoin(page_url, author_link["href"]) if author_link else None,
            "page_url": page_url,
            "scraped_at": utc_now(),
        }
