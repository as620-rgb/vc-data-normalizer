"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    PARSE_FUNDING = "parse_funding"
    CONVERT_TO_USD = "convert_to_usd"
    PARSE_BATCH = "parse_batch"


class Task(Enum):
    NORMALIZE_RECORDS = "normalize-records"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CNY = "CNY"


class Stage(Enum):
    PRE_SEED = "pre-seed"
    SEED = "seed"
    SERIES_A = "series-a"
    SERIES_B = "series-b"
    SERIES_C = "series-c"
    SERIES_D = "series-d"
    UNKNOWN = "unknown"


class Season(Enum):
    WINTER = "Winter"
    SPRING = "Spring"
    SUMMER = "Summer"
    FALL = "Fall"


FUNDING = (
    'A raw funding text: an amount with a currency and an optional round, e.g. "$5.5M Series A", "€20 million seed", '
    '"¥3000万", "GBP 750k", or "Undisclosed"'
)
BATCH = 'A raw YC batch text, e.g. "W24", "s2013", "Summer \'21", "X25" or "Fall 2024"'
AMOUNT = "An exact decimal number as text, e.g. 5500000 or 1234.5"


@dataclass
class RawRecord(Output):
    company: Annotated[str, "The company's name"]
    funding: Annotated[str, FUNDING]
    batch: Annotated[str, BATCH]


@dataclass
class NormalizeInput(Output):
    records: Annotated[list[RawRecord], "1 to 15 raw records"]


@dataclass
class NormalizedRecord(Output):
    company: Annotated[str, "The company's name, exactly as given"]
    disclosed: Annotated[bool, "Whether the funding text states an amount"]
    funding_usd: Annotated[int | None, "The amount in whole US dollars, as convert_to_usd gives it; null when not disclosed"]
    stage: Annotated[Stage, "The funding round; unknown when the text names none"]
    season: Annotated[Season, "The batch's season"]
    year: Annotated[int, "The batch's four-digit year"]


@dataclass
class NormalizeOutput(Output):
    records: Annotated[list[NormalizedRecord], "One record per input record, in the input's order"]
    total_usd: Annotated[int, "The sum of every disclosed funding_usd"]
    undisclosed: Annotated[int, "How many records do not disclose an amount"]


@dataclass
class FundingInput(Output):
    texts: Annotated[list[Annotated[str, FUNDING]], "1 to 15 funding texts"]


@dataclass
class ParsedFunding(Output):
    text: Annotated[str, "The funding text, as given"]
    disclosed: Annotated[bool, "Whether the text states an amount"]
    currency: Annotated[Currency | None, "The amount's currency; null when not disclosed"]
    amount: Annotated[str, "The amount in its own currency with its multiplier applied, as exact decimal text; empty when not disclosed"]
    stage: Annotated[Stage, "The round the text names; unknown when it names none"]


@dataclass
class FundingOutput(Output):
    parsed: Annotated[list[ParsedFunding], "One entry per text, in order"]


@dataclass
class Money(Output):
    currency: Currency
    amount: Annotated[str, AMOUNT]


@dataclass
class ConvertInput(Output):
    amounts: Annotated[list[Money], "1 to 15 amounts"]


@dataclass
class Converted(Output):
    currency: Currency
    amount: Annotated[str, AMOUNT]
    rate: Annotated[str, "US dollars per unit of the currency, from the plugin's fixed rate table"]
    usd: Annotated[int, "amount x rate, rounded to whole dollars, halves away from zero"]


@dataclass
class ConvertOutput(Output):
    converted: Annotated[list[Converted], "One entry per amount, in order"]


@dataclass
class BatchInput(Output):
    texts: Annotated[list[Annotated[str, BATCH]], "1 to 15 batch texts"]


@dataclass
class ParsedBatch(Output):
    text: Annotated[str, "The batch text, as given"]
    season: Season
    year: Annotated[int, "The four-digit year"]


@dataclass
class BatchOutput(Output):
    parsed: Annotated[list[ParsedBatch], "One entry per text, in order"]


TOOLS = {
    Tool.PARSE_FUNDING: (FundingInput, FundingOutput),
    Tool.CONVERT_TO_USD: (ConvertInput, ConvertOutput),
    Tool.PARSE_BATCH: (BatchInput, BatchOutput),
}
TASKS = {Task.NORMALIZE_RECORDS: (NormalizeInput, NormalizeOutput)}
