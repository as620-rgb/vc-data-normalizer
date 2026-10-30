"""The three tools' calls: each input must be readable by the rules, and each output must be what the rules give."""

from .checks import result
from .rules import MOST_RECORDS, parse_batch, parse_funding, to_usd


def _problems(items, read):
    if not 1 <= len(items) <= MOST_RECORDS:
        return f"give 1 to {MOST_RECORDS} entries, not {len(items)}"
    for item in items:
        try:
            read(item)
        except ValueError as error:
            return str(error)
    return None


def _input(items, read):
    problem = _problems(items, read)
    return result(False, problem) if problem else result(True, "input is valid")


def _output(expected, got):
    if len(expected) != len(got):
        return result(False, f"expected {len(expected)} entries, got {len(got)}")
    for index, (want, have) in enumerate(zip(expected, got)):
        if want != have:
            return result(False, f"entry {index}: expected {want}, got {have}")
    return result(True, f"{len(got)} entries follow the rules")


class Funding:
    @staticmethod
    def verify_input(value):
        return _input(value.texts, parse_funding)

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        expected = [{"text": text, **parse_funding(text)} for text in input_value.texts]
        got = [
            {
                "text": entry.text,
                "disclosed": entry.disclosed,
                "currency": entry.currency.value if entry.currency else None,
                "amount": entry.amount,
                "stage": entry.stage.value,
            }
            for entry in output_value.parsed
        ]
        return _output(expected, got)


class Convert:
    @staticmethod
    def verify_input(value):
        return _input(value.amounts, lambda money: to_usd(money.currency.value, money.amount))

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        expected = [
            (money.currency.value, money.amount, *to_usd(money.currency.value, money.amount))
            for money in input_value.amounts
        ]
        got = [(entry.currency.value, entry.amount, entry.rate, entry.usd) for entry in output_value.converted]
        return _output(expected, got)


class Batch:
    @staticmethod
    def verify_input(value):
        return _input(value.texts, parse_batch)

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        expected = [(text, *parse_batch(text)) for text in input_value.texts]
        got = [(entry.text, entry.season.value, entry.year) for entry in output_value.parsed]
        return _output(expected, got)
