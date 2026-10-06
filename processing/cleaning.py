"""Pure cleaning functions: no internet, no files."""
import re
from urllib.parse import urljoin

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

COLUMNS = ["source", "source_url", "name_or_title", "category", "price",
           "rating", "author", "tags", "description", "scraped_at"]


def clean_text(value):
    """Collapse all whitespace (incl. non-breaking); empty becomes None."""
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value):
    """Remove the curly/straight quote marks wrapping a quote."""
    text = clean_text(value)
    if text is None:
        return None
    return clean_text(text.strip('“”"'))


def clean_description(value):
    """Fix site artifacts: trailing '...more', mojibake, and a truncated copy of the text."""
    text = clean_text(value)
    if text is None:
        return None
    text = re.sub(r"\s*\.\.\.more$", "", text)
    if "Ã" in text or "â€" in text:                 # UTF-8 text that was decoded as cp1252
        try:
            text = text.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass                                    # leave it as-is if the fix doesn't apply
    if len(text) > 80:                              # drop a truncated first copy of the same text
        restart = text.find(text[:40], 1)
        if restart > 0:
            text = text[restart:]
    return clean_text(text)


def clean_price(raw):
    """'£51.77' -> 51.77; None if no number found."""
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    return float(match.group()) if match else None


def clean_rating(raw):
    """'star-rating Three' -> 3; None if no rating word found."""
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags):
    """Lowercase, de-duplicate, sort, join with ';'. No tags -> None."""
    cleaned = {clean_text(t).lower() for t in (tags or []) if clean_text(t)}
    return ";".join(sorted(cleaned)) or None


def normalize_url(url, base=None):
    """Return a full http(s) URL or None."""
    url = clean_text(url)
    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    elif base and not url.startswith(("http://", "https://")):
        url = urljoin(base, url)
    return url if url.startswith(("http://", "https://")) else None


def clean_book(raw):
    return {
        "source": "Books to Scrape",
        "source_url": normalize_url(raw.get("href")),
        "name_or_title": clean_text(raw.get("title")),
        "category": clean_text(raw.get("category_raw")),
        "price": clean_price(raw.get("price_raw")),
        "rating": clean_rating(raw.get("rating_raw")),
        "author": None,
        "tags": None,
        "description": clean_description(raw.get("description_raw")),
        "scraped_at": raw.get("scraped_at"),
    }


def clean_quote(raw):
    return {
        "source": "Quotes to Scrape",
        "source_url": normalize_url(raw.get("page_url")),   # page where the quote appeared
        "name_or_title": strip_quotes(raw.get("text")),
        "category": None,
        "price": None,
        "rating": None,
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": None,
        "scraped_at": raw.get("scraped_at"),
    }