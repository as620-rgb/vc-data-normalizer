from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import (
    BatchInput,
    BatchOutput,
    ConvertInput,
    ConvertOutput,
    FundingInput,
    FundingOutput,
    NormalizeInput,
    NormalizeOutput,
)
from plugin.normalize import convert_to_usd, parse_batch, parse_funding

RECORDS = [
    {"company": "Stripe", "funding": "€20 million seed", "batch": "S09"},
    {"company": "Groww", "funding": "Undisclosed", "batch": "W18"},
    {"company": "Meesho", "funding": "¥3000万 Series A", "batch": "Summer '16"},
    {"company": "Deel", "funding": "$5.5M", "batch": "w19"},
]
GOLD = {
    "records": [
        {"company": "Stripe", "disclosed": True, "funding_usd": 21600000, "stage": "seed", "season": "Summer", "year": 2009},
        {"company": "Groww", "disclosed": False, "funding_usd": None, "stage": "unknown", "season": "Winter", "year": 2018},
        {"company": "Meesho", "disclosed": True, "funding_usd": 4200000, "stage": "series-a", "season": "Summer", "year": 2016},
        {"company": "Deel", "disclosed": True, "funding_usd": 5500000, "stage": "unknown", "season": "Winter", "year": 2019},
    ],
    "total_usd": 31300000,
    "undisclosed": 1,
}


def check(output: dict, records: list[dict] = RECORDS, workspace: str = ".") -> dict:
    given = build_output({"records": records}, NormalizeInput)
    return verifier.verify_task("normalize-records", given, build_output(output, NormalizeOutput), None, workspace)


def failing(verdict: dict) -> list[str]:
    return [entry["id"] for entry in verdict["details"]["constraints"] if not entry["ok"]]


def changed(index: int, **fields) -> dict:
    records = [dict(record) for record in GOLD["records"]]
    records[index].update(fields)
    return {**GOLD, "records": records}


def test_approves_the_correct_answer() -> None:
    verdict = check(GOLD)
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_the_tools_build_the_correct_answer(tmp_path: Path) -> None:
    # The agent's plan, scripted: three tool calls, each checked like NanoAgent checks it, then the submission.
    funding_in = build_output({"texts": [r["funding"] for r in RECORDS]}, FundingInput)
    funding = build_output(plain_output(parse_funding(funding_in, tmp_path)), FundingOutput)
    assert verifier.verify_output("parse_funding", funding_in, funding, str(tmp_path))["valid"] is True
    disclosed = [p for p in funding.parsed if p.disclosed]
    convert_in = build_output({"amounts": [{"currency": p.currency.value, "amount": p.amount} for p in disclosed]}, ConvertInput)
    converted = build_output(plain_output(convert_to_usd(convert_in, tmp_path)), ConvertOutput)
    assert verifier.verify_output("convert_to_usd", convert_in, converted, str(tmp_path))["valid"] is True
    batch_in = build_output({"texts": [r["batch"] for r in RECORDS]}, BatchInput)
    batches = build_output(plain_output(parse_batch(batch_in, tmp_path)), BatchOutput)
    assert verifier.verify_output("parse_batch", batch_in, batches, str(tmp_path))["valid"] is True
    usd = iter(c.usd for c in converted.converted)
    records = [
        {"company": r["company"], "disclosed": p.disclosed, "funding_usd": next(usd) if p.disclosed else None,
         "stage": p.stage.value, "season": b.season.value, "year": b.year}
        for r, p, b in zip(RECORDS, funding.parsed, batches.parsed)
    ]
    output = {"records": records, "total_usd": sum(r["funding_usd"] or 0 for r in records), "undisclosed": 1}
    assert output == GOLD and check(output)["valid"] is True


def test_rejects_an_unconverted_amount() -> None:
    verdict = check(changed(0, funding_usd=20000000))  # the totals stay right
    assert failing(verdict) == ["funding-usd-exact"] and "Stripe" in verdict["message"]


def test_rejects_a_wrong_stage_season_or_year() -> None:
    assert failing(check(changed(2, stage="series-b"))) == ["stage-exact"]
    assert failing(check(changed(3, season="Summer"))) == ["season-exact"]
    assert failing(check(changed(3, year=2009))) == ["year-exact"]


def test_rejects_a_made_up_amount_for_an_undisclosed_record() -> None:
    verdict = check({**changed(1, disclosed=True, funding_usd=0)})
    assert set(failing(verdict)) == {"disclosed-exact", "funding-usd-exact"}
    assert "usd-only-when-disclosed" in failing(check(changed(1, funding_usd=0)))


def test_rejects_wrong_totals() -> None:
    assert failing(check({**GOLD, "total_usd": 31300001})) == ["total-usd"]
    assert failing(check({**GOLD, "undisclosed": 0})) == ["undisclosed-count"]


def test_rejects_missing_reordered_or_renamed_records() -> None:
    assert {"one-per-record", "same-companies"} <= set(failing(check({**GOLD, "records": GOLD["records"][:3]})))
    assert "same-companies" in failing(check({**GOLD, "records": GOLD["records"][::-1]}))
    assert "same-companies" in failing(check(changed(0, company="stripe")))


def test_boundary_all_undisclosed_and_single_record() -> None:
    records = [{"company": "A", "funding": "n/a", "batch": "X25"}]
    output = {"records": [{"company": "A", "disclosed": False, "funding_usd": None, "stage": "unknown",
                           "season": "Spring", "year": 2025}], "total_usd": 0, "undisclosed": 1}
    assert check(output, records)["valid"] is True


def test_rejects_an_unreadable_or_oversized_task() -> None:
    bad = [{"company": "A", "funding": "about five million", "batch": "W24"}]
    verdict = check({"records": [], "total_usd": 0, "undisclosed": 0}, bad)
    assert verdict["valid"] is False and "cannot be normalized" in verdict["message"]
    assert check({"records": [], "total_usd": 0, "undisclosed": 0}, [])["valid"] is False
    assert check(GOLD, RECORDS * 4)["valid"] is False  # 16 records


def test_tool_checks_refuse_bad_inputs_and_tampered_outputs(tmp_path: Path) -> None:
    assert verifier.verify_input("parse_funding", build_output({"texts": ["5M"]}, FundingInput))["valid"] is False
    assert verifier.verify_input("parse_batch", build_output({"texts": ["Autumn 2020"]}, BatchInput))["valid"] is False
    bad_amount = build_output({"amounts": [{"currency": "USD", "amount": "-5"}]}, ConvertInput)
    assert verifier.verify_input("convert_to_usd", bad_amount)["valid"] is False
    with pytest.raises(ValueError):
        convert_to_usd(bad_amount, tmp_path)
    given = build_output({"amounts": [{"currency": "EUR", "amount": "100"}]}, ConvertInput)
    tampered = build_output({"converted": [{"currency": "EUR", "amount": "100", "rate": "1.08", "usd": 100}]}, ConvertOutput)
    assert verifier.verify_output("convert_to_usd", given, tampered, str(tmp_path))["valid"] is False
