"""
Data Normalizer Verifier (Task 5)
"""

from typing import Any


def verify_task(task_input: Any, agent_output: Any, workspace_path: str) -> dict:
    constraints = []

    # 1. Verification of Output Structure Existence
    has_records = hasattr(agent_output, "normalized_records") and isinstance(agent_output.normalized_records, list)
    if not has_records:
        return {
            "score": 0.0,
            "constraints": [{
                "id": "shape-check",
                "ok": False,
                "message": "agent_output missing 'normalized_records' list"
            }]
        }

    records = agent_output.normalized_records

    # ---- Constraint 1: The number of output entries is non-zero, and the count is accurate. ----
    ok_count = len(records) > 0 and len(records) == getattr(agent_output, "total_processed", 0)
    constraints.append({
        "id": "non-empty-normalized-records",
        "ok": ok_count,
        "message": "" if ok_count else "Normalized records list is empty or count mismatch"
    })

    # ---- Constraint 2: Financing Amount Value Conversion Assertion (Ensure successful cleansing into a float value) ----
    ok_funding = all(isinstance(getattr(r, "funding_usd", None), (int, float)) and getattr(r, "funding_usd", -1) >= 0 for r in records)
    constraints.append({
        "id": "funding-numeric-check",
        "ok": ok_funding,
        "message": "" if ok_funding else "funding_usd must be non-negative float"
    })

    # ---- Constraint 3: Batch specification format assertion (must be in the form 'SEASON YEAR') ----
    ok_batch = all(" " in getattr(r, "standard_batch", "") for r in records)
    constraints.append({
        "id": "standard-batch-format",
        "ok": ok_batch,
        "message": "" if ok_batch else "standard_batch must follow 'SEASON YEAR' format"
    })

    score = 1.0 if all(c["ok"] for c in constraints) else 0.0
    return {
        "score": score,
        "constraints": constraints
    }
