from processing.deduplication import find_duplicates


def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None, "price": 10.0}
    records = [{**base, "name_or_title": "Example Book Title"},
               {**base, "name_or_title": "  Example Book Title "},
               {**base, "name_or_title": "EXAMPLE BOOK TITLE"}]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2


def test_same_title_different_price_is_not_duplicate():
    # Real case found on the site: two different books called "The Star-Touched Queen"
    base = {"source": "Books to Scrape", "author": None, "name_or_title": "The Star-Touched Queen"}
    unique, dupes = find_duplicates([{**base, "price": 46.02}, {**base, "price": 32.30}])
    assert len(unique) == 2 and len(dupes) == 0


def test_quotes_use_author_and_first_50_chars():
    q = {"source": "Quotes to Scrape", "name_or_title": "Same text", "author": "A"}
    other = {**q, "author": "B"}
    unique, dupes = find_duplicates([q, {**q, "author": " a "}, other])
    assert len(unique) == 2 and len(dupes) == 1


def test_same_title_different_source_is_not_duplicate():
    r1 = {"source": "Books to Scrape", "name_or_title": "T", "author": None, "price": 1.0}
    r2 = {"source": "Quotes to Scrape", "name_or_title": "T", "author": None}
    assert len(find_duplicates([r1, r2])[0]) == 2