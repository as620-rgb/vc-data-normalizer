"""The normalization rules, as plain values: pure standard library, so both the tools and the sandboxed verifier
use them. tests/test_rules.py pins them against hand-worked answers."""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MOST_RECORDS = 15
# US dollars per unit: a fixed table (not live rates), so every run converts the same way.
RATES = {"USD": Decimal(1), "EUR": Decimal("1.08"), "GBP": Decimal("1.27"), "CNY": Decimal("0.14")}
CURRENCY_WORDS = {
    "$": "USD", "us$": "USD", "usd": "USD",
    "€": "EUR", "eur": "EUR",
    "£": "GBP", "gbp": "GBP",
    "¥": "CNY", "cny": "CNY", "rmb": "CNY",
}
MULTIPLIERS = {
    "k": 10**3, "thousand": 10**3,
    "m": 10**6, "mn": 10**6, "million": 10**6,
    "b": 10**9, "bn": 10**9, "billion": 10**9,
    "万": 10**4, "亿": 10**8,
}
UNDISCLOSED = {"", "undisclosed", "not disclosed", "n/a", "unknown"}
AMOUNT = re.compile(
    r"(?P<pre>us\$|\$|€|£|¥|usd|eur|gbp|cny|rmb)?\s*"
    r"(?P<number>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?:(?P<cjk>万|亿)|(?P<word>thousand|million|billion|mn|bn|k|m|b)(?![a-z]))?\s*"
    r"(?P<post>usd|eur|gbp|cny|rmb)?(?![a-z])",
    re.IGNORECASE,
)
STAGES = [
    (re.compile(r"\bpre-?seed\b", re.IGNORECASE), "pre-seed"),
    (re.compile(r"(?<!-)\bseed\b", re.IGNORECASE), "seed"),
    (re.compile(r"\bseries\s+([a-d])\b", re.IGNORECASE), "series-"),
]
SEASONS = {"w": "Winter", "x": "Spring", "s": "Summer", "f": "Fall"}
BATCH = re.compile(r"(?P<season>winter|spring|summer|fall|[wxsf])\s*'?(?P<year>\d{4}|\d{2})", re.IGNORECASE)
FIRST_YEAR, LAST_YEAR = 2005, 2030


def plain_decimal(value):
    """A Decimal as plain text without exponent or trailing zeros: 5500000, 1234.5."""
    text = format(value.normalize(), "f")
    return text


def stage_of(text):
    found = []
    rest = text
    for pattern, name in STAGES:
        for match in pattern.finditer(rest):
            found.append(name + match.group(1).lower() if name == "series-" else name)
        rest = pattern.sub(" ", rest)
    if len(found) > 1:
        raise ValueError(f"{text!r} names more than one round: {found}")
    return (found[0] if found else "unknown"), rest


def parse_funding(text):
    """{disclosed, currency, amount, stage} of a funding text, or ValueError naming why it cannot be read."""
    stage, rest = stage_of(text)
    amounts = list(AMOUNT.finditer(rest))
    if not amounts:
        if " ".join(rest.split()).casefold() in UNDISCLOSED:
            return {"disclosed": False, "currency": None, "amount": "", "stage": stage}
        raise ValueError(f"{text!r} states no amount and is not one of {sorted(UNDISCLOSED)}")
    if len(amounts) > 1:
        raise ValueError(f"{text!r} states more than one amount")
    match = amounts[0]
    leftover = (rest[: match.start()] + rest[match.end() :]).strip()
    if leftover:
        raise ValueError(f"{text!r} has text that is neither an amount nor a round: {leftover!r}")
    marks = {CURRENCY_WORDS[match.group(side).lower()] for side in ("pre", "post") if match.group(side)}
    if len(marks) != 1:
        raise ValueError(f"{text!r} must name exactly one currency")
    multiplier = MULTIPLIERS[(match.group("cjk") or match.group("word") or "").lower()] if (
        match.group("cjk") or match.group("word")
    ) else 1
    amount = Decimal(match.group("number").replace(",", "")) * multiplier
    return {"disclosed": True, "currency": marks.pop(), "amount": plain_decimal(amount), "stage": stage}


def to_usd(currency, amount):
    """(rate as text, whole US dollars rounded halves away from zero), or ValueError."""
    if currency not in RATES:
        raise ValueError(f"no rate for {currency!r}")
    try:
        value = Decimal(amount)
    except InvalidOperation:
        raise ValueError(f"{amount!r} is not a decimal number") from None
    if not value.is_finite() or value < 0:
        raise ValueError(f"{amount!r} must be a finite number, 0 or more")
    rate = RATES[currency]
    return plain_decimal(rate), int((value * rate).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def parse_batch(text):
    """(season, four-digit year) of a batch text, or ValueError."""
    match = BATCH.fullmatch(text.strip())
    if not match:
        raise ValueError(f"{text!r} is not a batch such as W24, S2013 or Summer 2021")
    word = match.group("season").lower()
    season = SEASONS[word[0]] if len(word) == 1 else word.capitalize()
    digits = match.group("year")
    year = 2000 + int(digits) if len(digits) == 2 else int(digits)
    if not FIRST_YEAR <= year <= LAST_YEAR:
        raise ValueError(f"{text!r}: year {year} is outside {FIRST_YEAR} to {LAST_YEAR}")
    return season, year


def normalize(record):
    """The normalized form of one raw record {company, funding, batch}, as plain values."""
    funding = parse_funding(record["funding"])
    season, year = parse_batch(record["batch"])
    usd = to_usd(funding["currency"], funding["amount"])[1] if funding["disclosed"] else None
    return {
        "company": record["company"],
        "disclosed": funding["disclosed"],
        "funding_usd": usd,
        "stage": funding["stage"],
        "season": season,
        "year": year,
    }
