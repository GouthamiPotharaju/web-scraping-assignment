"""Shared networking code: session with retries, fetch helper, pagination loop."""
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Session with a User-Agent and retries (1s, 2s, 4s backoff) on temporary errors."""
    session = requests.Session()
    session.headers.update({"User-Agent": "ScrapingAssignment/1.0 (learning project)"})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BaseScraper:
    """Subclasses set source_name/start_url and implement parse_page()."""

    source_name = ""
    start_url = ""

    def __init__(self, session=None, delay=0.5, timeout=10, max_pages=None):
        self.session = session or create_session()
        self.delay = delay
        self.timeout = timeout
        self.max_pages = max_pages      # None = follow "next" until it ends
        self.pages_scraped = 0
        self.parse_errors = 0
        self.failed_urls = []

    def fetch(self, url):
        """Download one page and return a BeautifulSoup, or None on failure."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"   # keeps the £ symbol correct
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            self.failed_urls.append(url)
            return None
        finally:
            time.sleep(self.delay)        # be polite to the server
        return BeautifulSoup(response.text, "lxml")

    def parse_page(self, soup, page_url) -> list:
        raise NotImplementedError

    def scrape(self) -> list:
        """Follow li.next > a until there is no next page."""
        url, page, records = self.start_url, 1, []
        while url:
            if self.max_pages and page > self.max_pages:
                logger.info("[%s] max_pages=%d reached, stopping", self.source_name, self.max_pages)
                break
            logger.info("[%s] Page %d: %s", self.source_name, page, url)
            soup = self.fetch(url)
            if soup is None:
                break                     # stop this source; the other one still runs
            records.extend(self.parse_page(soup, url))
            self.pages_scraped += 1
            next_link = soup.select_one("li.next > a")
            url = urljoin(url, next_link["href"]) if next_link and next_link.get("href") else None
            page += 1
        logger.info("[%s] Done: %d raw records from %d pages",
                    self.source_name, len(records), self.pages_scraped)
        return records
