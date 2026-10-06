"""Offline scraper tests using a fake session (no internet)."""
import requests
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper


class FakeResponse:
    def __init__(self, text):
        self.text, self.encoding = text, None

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, timeout=None):
        if url not in self.pages:
            raise requests.ConnectionError("boom")
        return FakeResponse(self.pages[url])


def book(title, href, price="£51.77", rating="Three"):
    return (f'<article class="product_pod"><p class="star-rating {rating}"></p>'
            f'<h3><a href="{href}" title="{title}">{title[:5]}...</a></h3>'
            f'<p class="price_color">{price}</p></article>')


def test_books_pagination_and_missing_elements():
    p1 = ("<html><body>" + book("Book A", "a/index.html") +
          '<article class="product_pod"><h3></h3></article>'          # missing everything
          '<li class="next"><a href="page-2.html">next</a></li></body></html>')
    p2 = "<html><body>" + book("Book B", "b/index.html") + "</body></html>"
    s = BooksScraper(session=FakeSession({"https://books.toscrape.com/": p1,
                                          "https://books.toscrape.com/page-2.html": p2}),
                     delay=0, fetch_details=False)
    recs = s.scrape()
    assert s.pages_scraped == 2 and len(recs) == 3
    assert recs[0]["title"] == "Book A" and recs[0]["price_raw"] == "£51.77"
    assert recs[0]["href"] == "https://books.toscrape.com/a/index.html"
    assert recs[1]["title"] is None            # kept as raw; validation rejects it later


def test_failed_page_stops_source_but_keeps_earlier_records():
    p1 = ("<html>" + book("Book A", "a.html") +
          '<li class="next"><a href="missing.html">n</a></li></html>')
    s = BooksScraper(session=FakeSession({"https://books.toscrape.com/": p1}),
                     delay=0, fetch_details=False)
    assert len(s.scrape()) == 1 and len(s.failed_urls) == 1


def test_book_detail_parsing():
    html = ('<ul class="breadcrumb"><li><a>Home</a></li><li><a>Books</a></li>'
            '<li><a>Travel</a></li><li>Title</li></ul>'
            '<div id="product_description"><h2>Desc</h2></div><p>Nice book.</p>')
    from bs4 import BeautifulSoup
    cat, desc = BooksScraper(session=FakeSession({}), delay=0).parse_detail(BeautifulSoup(html, "lxml"))
    assert cat == "Travel" and desc == "Nice book."


def test_quotes_pagination():
    q = ('<div class="quote"><span class="text">\u201cHi\u201d</span>'
         '<span>by <small class="author">Al</small><a href="/author/Al">(about)</a></span>'
         '<div class="tags"><a class="tag">x</a><a class="tag">y</a></div></div>')
    pages = {"https://quotes.toscrape.com/": q + '<li class="next"><a href="/page/2/">n</a></li>',
             "https://quotes.toscrape.com/page/2/": q}
    s = QuotesScraper(session=FakeSession(pages), delay=0)
    recs = s.scrape()
    assert len(recs) == 2 and recs[0]["tags"] == ["x", "y"]
    assert recs[0]["author_href"] == "https://quotes.toscrape.com/author/Al"
