"""Verdict helpers shared by the tool verifiers. Pure functions of their arguments."""

MOST = 10  # list entries a constraint's expected or actual shows


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def compact(value):
    if isinstance(value, list) and len(value) > MOST:
        return value[:MOST] + [f"... {len(value) - MOST} more"]
    return value


def constraint(identifier, text, ok, expected=None, actual=None, message=""):
    """One check: ok True (holds) or False (fails), with what was expected and found when they say something."""
    return {
        "id": identifier,
        "constraint": text,
        "ok": ok,
        "expected": compact(expected),
        "actual": compact(actual),
        "message": "" if ok else (message or text),
    }


def verdict(constraints):
    """Valid only when every constraint holds; the score is the share that holds; the message names the first failure."""
    failed = [entry for entry in constraints if not entry["ok"]]
    score = (len(constraints) - len(failed)) / len(constraints)
    if not failed:
        return result(True, f"all {len(constraints)} checks hold", score=1.0, constraints=constraints)
    more = f" (+{len(failed) - 1} more)" if len(failed) > 1 else ""
    return result(False, f"{failed[0]['id']}: {failed[0]['message']}{more}", score=score, constraints=constraints)
