from processing.cleaning import (clean_description, clean_price, clean_rating, clean_tags, clean_text,
                                 clean_book, clean_quote, normalize_url, strip_quotes)


def test_clean_text():
    assert clean_text("  Hello \n\xa0 World ") == "Hello World"
    assert clean_text("   ") is None and clean_text(None) is None


def test_strip_quotes():
    assert strip_quotes("\u201cThe world.\u201d ") == "The world."


def test_clean_price():
    assert clean_price("£51.77") == 51.77
    assert clean_price("Â£1,051.77") == 1051.77
    assert clean_price("free") is None and clean_price(None) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("star-rating") is None


def test_clean_tags():
    assert clean_tags(["Love", " books", "love"]) == "books;love"
    assert clean_tags([]) is None


def test_normalize_url():
    assert normalize_url("/a/b", base="https://x.com/q/") == "https://x.com/a/b"
    assert normalize_url("not a url") is None


def test_record_builders():
    b = clean_book({"title": " A  Book ", "href": "https://x.com/b", "price_raw": "£5.00",
                    "rating_raw": "star-rating Five", "scraped_at": "t"})
    assert b["price"] == 5.0 and b["rating"] == 5 and b["author"] is None
    q = clean_quote({"text": "\u201cHi\u201d", "author": " Al ", "tags": ["B", "a"],
                     "page_url": "https://q.com/", "scraped_at": "t"})
    assert q["name_or_title"] == "Hi" and q["tags"] == "a;b" and q["price"] is None


def test_clean_description():
    dup = "A" * 10 + " It is a long enough sentence to be repeated here " + "x " * 20
    text = dup[:60] + " " + dup + " ...more"
    assert clean_description(text) == dup.strip()
    assert clean_description("Peu motivÃ© par lâ€™enseignement") == "Peu motivé par l’enseignement"