"""Fingerprint-based duplicate detection (duplicates are removed, first kept)."""
import hashlib
import re

BOOKS = "Books to Scrape"


def make_fingerprint(rec):
    name = rec.get("name_or_title") or ""
    if rec.get("source") == BOOKS:
        key = f'{rec["source"]} {name}'                          # source + title ...
    else:
        key = f'{rec.get("source")} {rec.get("author") or ""} {name[:50]}'  # source + author + 50 chars
    key = re.sub(r"[^\w\s]", "", key.lower())    # lowercase, drop punctuation
    key = " ".join(key.split())                  # collapse spaces
    if rec.get("source") == BOOKS:               # ... + price (different books can share a title)
        price = rec.get("price")
        key += f' | {price:.2f}' if isinstance(price, (int, float)) else ' | none'
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records):
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes