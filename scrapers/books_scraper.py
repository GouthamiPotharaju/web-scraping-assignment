"""Books to Scrape: listing selectors, detail-page enrichment, pagination."""
import logging
from urllib.parse import urljoin

from .base_scraper import BaseScraper, utc_now

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    source_name = "Books to Scrape"
    start_url = "https://books.toscrape.com/"

    def __init__(self, *args, fetch_details=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_details = fetch_details

    def parse_page(self, soup, page_url):
        records = []
        for article in soup.select("article.product_pod"):
            try:
                records.append(self.parse_book(article, page_url))
            except Exception as exc:      # one bad record must not stop the page
                self.parse_errors += 1
                logger.warning("[Books] Skipped a record on %s: %s", page_url, exc)
        return records

    def parse_book(self, article, page_url):
        link = article.select_one("h3 > a")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        return {
            "title": link.get("title") if link else None,   # full title is in the attribute
            "href": urljoin(page_url, link["href"]) if link and link.get("href") else None,
            "price_raw": price.get_text() if price else None,
            "rating_raw": " ".join(rating.get("class", [])) if rating else None,
            "category_raw": None,
            "description_raw": None,
            "scraped_at": utc_now(),
        }

    def parse_detail(self, soup):
        """Category (breadcrumb) and description from a book's detail page."""
        crumbs = soup.select("ul.breadcrumb li a")
        category = crumbs[-1].get_text() if len(crumbs) >= 3 else None
        desc_header = soup.select_one("#product_description")
        desc_p = desc_header.find_next_sibling("p") if desc_header else None
        return category, desc_p.get_text() if desc_p else None

    def scrape(self):
        records = super().scrape()
        if self.fetch_details:
            logger.info("[Books] Fetching %d detail pages", len(records))
            for rec in records:
                if not rec["href"]:
                    continue
                soup = self.fetch(rec["href"])
                if soup is None:
                    continue              # leave category/description empty
                try:
                    rec["category_raw"], rec["description_raw"] = self.parse_detail(soup)
                except Exception as exc:
                    self.parse_errors += 1
                    logger.warning("[Books] Detail parse failed %s: %s", rec["href"], exc)
        return records
