from __future__ import annotations

import pytest

from verifier.rules import normalize, parse_batch, parse_funding, to_usd


@pytest.mark.parametrize(
    ("text", "disclosed", "currency", "amount", "stage"),
    [
        ("$5.5M Series A", True, "USD", "5500000", "series-a"),
        ("€20 million seed", True, "EUR", "20000000", "seed"),
        ("¥3000万", True, "CNY", "30000000", "unknown"),
        ("¥1.2亿 Series B", True, "CNY", "120000000", "series-b"),
        ("GBP 750k pre-seed", True, "GBP", "750000", "pre-seed"),
        ("750K gbp", True, "GBP", "750000", "unknown"),
        ("US$1,250,000", True, "USD", "1250000", "unknown"),
        ("$2.5bn Series D", True, "USD", "2500000000", "series-d"),
        ("$0", True, "USD", "0", "unknown"),
        ("$5M USD", True, "USD", "5000000", "unknown"),
        ("12.5 EUR", True, "EUR", "12.5", "unknown"),
        ("Undisclosed", False, None, "", "unknown"),
        ("  n/a ", False, None, "", "unknown"),
        ("Undisclosed Series A", False, None, "", "series-a"),
        ("", False, None, "", "unknown"),
    ],
)
def test_funding_texts(text, disclosed, currency, amount, stage) -> None:
    assert parse_funding(text) == {"disclosed": disclosed, "currency": currency, "amount": amount, "stage": stage}


@pytest.mark.parametrize(
    "text",
    ["5M", "$5M EUR", "$5M and $2M", "$5.5MM", "around $5M", "Series A Series B $1M", "lots of money", "$"],
)
def test_unreadable_funding_texts_are_refused(text) -> None:
    with pytest.raises(ValueError):
        parse_funding(text)


@pytest.mark.parametrize(
    ("currency", "amount", "usd"),
    [
        ("USD", "5500000", 5500000),
        ("EUR", "20000000", 21600000),
        ("GBP", "750000", 952500),
        ("CNY", "30000000", 4200000),
        ("EUR", "12.5", 14),  # 13.5 rounds half away from zero
        ("GBP", "0.5", 1),  # 0.635
        ("CNY", "3", 0),  # 0.42
        ("USD", "0", 0),
    ],
)
def test_conversion(currency, amount, usd) -> None:
    assert to_usd(currency, amount)[1] == usd


@pytest.mark.parametrize(("currency", "amount"), [("JPY", "1"), ("USD", "-1"), ("USD", "abc"), ("USD", "NaN"), ("USD", "Infinity")])
def test_bad_conversions_are_refused(currency, amount) -> None:
    with pytest.raises(ValueError):
        to_usd(currency, amount)


@pytest.mark.parametrize(
    ("text", "season", "year"),
    [
        ("W24", "Winter", 2024),
        ("s2013", "Summer", 2013),
        ("Summer '21", "Summer", 2021),
        ("X25", "Spring", 2025),
        ("Fall 2024", "Fall", 2024),
        ("  winter 05 ", "Winter", 2005),
        ("F30", "Fall", 2030),
    ],
)
def test_batches(text, season, year) -> None:
    assert parse_batch(text) == (season, year)


@pytest.mark.parametrize("text", ["W2004", "S31", "Autumn 2020", "2021", "W", "Summer 2021 extra"])
def test_unreadable_batches_are_refused(text) -> None:
    with pytest.raises(ValueError):
        parse_batch(text)


def test_a_whole_record() -> None:
    assert normalize({"company": "Stripe", "funding": "€20 million seed", "batch": "S09"}) == {
        "company": "Stripe", "disclosed": True, "funding_usd": 21600000, "stage": "seed", "season": "Summer", "year": 2009,
    }
