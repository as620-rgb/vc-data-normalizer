"""
VC Financial & Industry Data Normalizer (Task 5)
Typed input and output declarations using nanoagent.plugin.contract standards.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Optional
from slimconfig import Output


class Tool(Enum):
    NORMALIZE_FINANCIALS = "normalize_financials"
    CATEGORIZE_INDUSTRY = "categorize_industry"


class Task(Enum):
    DATA_NORMALIZER = "data-normalizer"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CNY = "CNY"


# Metadata Annotations
RAW_FUNDING = "Raw funding amount text, e.g., '$5.5M', '¥3000万', 'Undisclosed', or '€20M Series A'"
RAW_TAGS = "List of raw unstandardized industry tags, e.g., ['AI', 'Generative AI', 'SaaS']"


@dataclass
class RawCompanyData(Output):
    company_name: str
    funding_text: Annotated[str, RAW_FUNDING]
    tags: Annotated[list[str], RAW_TAGS]


@dataclass
class NormalizerInput(Output):
    companies: list[RawCompanyData]
    target_currency: Currency = Currency.USD


@dataclass
class NormalizedCompany(Output):
    company_name: str
    funding_usd: Optional[float]
    funding_stage: Optional[str]
    primary_industry: str
    secondary_tags: list[str]


@dataclass
class NormalizerOutput(Output):
    normalized_records: list[NormalizedCompany]
    processed_count: int
    has_unparsed_funding: bool


TOOLS = {
    Tool.NORMALIZE_FINANCIALS: (RawCompanyData, NormalizedCompany),
}

TASKS = {
    Task.DATA_NORMALIZER: (NormalizerInput, NormalizerOutput),
}