from processing.validation import validate_record

GOOD = {"source": "Books to Scrape", "name_or_title": "X", "source_url": "https://a.com",
        "price": 1.5, "rating": 3}


def test_valid():
    assert validate_record(GOOD) == []


def test_each_rule():
    assert "unknown_source" in validate_record({**GOOD, "source": "Nope"})
    assert "missing_name" in validate_record({**GOOD, "name_or_title": None})
    assert "invalid_url" in validate_record({**GOOD, "source_url": "ftp://a"})
    assert "invalid_price" in validate_record({**GOOD, "price": -1})
    assert "invalid_rating" in validate_record({**GOOD, "rating": 9})


def test_none_price_rating_ok():
    assert validate_record({**GOOD, "price": None, "rating": None}) == []
