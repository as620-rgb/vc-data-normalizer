"""The three normalization tools. The rules themselves live in verifier/rules.py, the one copy both the tools
and the verifier read; tests/test_rules.py pins them against hand-worked answers."""

from __future__ import annotations

from pathlib import Path

from contract import (
    BatchInput,
    BatchOutput,
    Converted,
    ConvertInput,
    ConvertOutput,
    Currency,
    FundingInput,
    FundingOutput,
    ParsedBatch,
    ParsedFunding,
    Season,
    Stage,
)
from verifier import rules


def _count(items: list, what: str) -> None:
    if not 1 <= len(items) <= rules.MOST_RECORDS:
        raise ValueError(f"give 1 to {rules.MOST_RECORDS} {what}, not {len(items)}")


def parse_funding(request: FundingInput, workspace: Path) -> FundingOutput:
    _count(request.texts, "texts")
    parsed = []
    for text in request.texts:
        found = rules.parse_funding(text)
        parsed.append(
            ParsedFunding(
                text=text,
                disclosed=found["disclosed"],
                currency=Currency(found["currency"]) if found["currency"] else None,
                amount=found["amount"],
                stage=Stage(found["stage"]),
            )
        )
    return FundingOutput(parsed=parsed)


def convert_to_usd(request: ConvertInput, workspace: Path) -> ConvertOutput:
    _count(request.amounts, "amounts")
    converted = []
    for money in request.amounts:
        rate, usd = rules.to_usd(money.currency.value, money.amount)
        converted.append(Converted(currency=money.currency, amount=money.amount, rate=rate, usd=usd))
    return ConvertOutput(converted=converted)


def parse_batch(request: BatchInput, workspace: Path) -> BatchOutput:
    _count(request.texts, "texts")
    parsed = []
    for text in request.texts:
        season, year = rules.parse_batch(text)
        parsed.append(ParsedBatch(text=text, season=Season(season), year=year))
    return BatchOutput(parsed=parsed)
