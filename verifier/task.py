"""normalize-records: every submitted record against the rules applied to the task's own input."""

from .checks import constraint, result, verdict
from .rules import MOST_RECORDS, normalize

FIELDS = ("disclosed", "funding_usd", "stage", "season", "year")


def plain(record):
    return {
        "company": record.company,
        "disclosed": record.disclosed,
        "funding_usd": record.funding_usd,
        "stage": record.stage.value,
        "season": record.season.value,
        "year": record.year,
    }


def verify_task(arguments, output, reference, workspace):
    raw = [{"company": r.company, "funding": r.funding, "batch": r.batch} for r in arguments.records]
    if not 1 <= len(raw) <= MOST_RECORDS:
        return result(False, f"the task must give 1 to {MOST_RECORDS} records, not {len(raw)}")
    try:
        expected = [normalize(record) for record in raw]
    except ValueError as error:
        return result(False, f"the task's input cannot be normalized: {error}")
    got = [plain(record) for record in output.records]
    total = sum(record["funding_usd"] for record in expected if record["disclosed"])
    undisclosed = sum(1 for record in expected if not record["disclosed"])

    same_length = len(got) == len(expected)
    names = [record["company"] for record in got] == [record["company"] for record in expected]
    wrong = {field: [] for field in FIELDS}
    if same_length and names:
        for want, have in zip(expected, got):
            for field in FIELDS:
                if want[field] != have[field]:
                    wrong[field].append(f"{want['company']}: expected {want[field]!r}, got {have[field]!r}")
    consistent = [r["company"] for r in got if r["disclosed"] != (r["funding_usd"] is not None)]
    aligned = same_length and names

    checks = [
        constraint("one-per-record", "one output record per input record", same_length, len(expected), len(got)),
        constraint("same-companies", "records keep the input's companies and order", names,
                   [r["company"] for r in expected], [r["company"] for r in got]),
        constraint("usd-only-when-disclosed", "funding_usd is null exactly when the amount is not disclosed",
                   not consistent, [], consistent, f"inconsistent records: {consistent}"),
    ]
    for field in FIELDS:
        problems = wrong[field]
        checks.append(constraint(
            f"{field.replace('_', '-')}-exact", f"every record's {field} follows the rules", aligned and not problems,
            None, problems, problems[0] if problems else "records are not aligned with the input",
        ))
    checks += [
        constraint("total-usd", "total_usd is the sum of the disclosed amounts", output.total_usd == total,
                   total, output.total_usd),
        constraint("undisclosed-count", "undisclosed counts the records without an amount",
                   output.undisclosed == undisclosed, undisclosed, output.undisclosed),
    ]
    return verdict(checks)
