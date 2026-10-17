"""
VC Data Normalization Tools (Task 5)
"""

import re
from contract import (
    NormalizerInput,
    NormalizerOutput,
    NormalizedVCRecord,
)


def parse_funding_to_usd(raw_amount: str) -> float:
    """Standardize and convert messy text-based monetary amounts (e.g., '$5.5M', '500K USD') into USD float values."""
    if not raw_amount:
        return 0.0
    
    text = raw_amount.upper().replace(",", "").strip()
    multiplier = 1.0
    
    if "M" in text or "MILLION" in text:
        multiplier = 1_000_000.0
    elif "K" in text or "THOUSAND" in text:
        multiplier = 1_000.0
    elif "B" in text or "BILLION" in text:
        multiplier = 1_000_000_000.0

    # Extract purely numeric floating-point numbers
    numbers = re.findall(r"\d+\.?\d*", text)
    if not numbers:
        return 0.0
    
    val = float(numbers[0]) * multiplier
    
    # Simple currency symbol handling (assuming 1 RMB = 0.14 USD)
    if "¥" in text or "RMB" in text or "CNY" in text:
        val *= 0.14
        
    return round(val, 2)


def normalize_batch_format(raw_batch: str) -> str:
    """Standardize Batch format (e.g., 'w24' -> 'WINTER 2024')"""
    text = raw_batch.upper().strip()
    year_match = re.search(r"\d{2,4}", text)
    
    year = year_match.group(0) if year_match else "2026"
    if len(year) == 2:
        year = f"20{year}"
        
    if "W" in text or "WINTER" in text:
        season = "WINTER"
    elif "S" in text or "SUMMER" in text:
        season = "SUMMER"
    elif "F" in text or "FALL" in text:
        season = "FALL"
    else:
        season = "SPRING"
        
    return f"{season} {year}"


def normalize_data_tool(input_data: NormalizerInput) -> NormalizerOutput:
    cleaned_list: list[NormalizedVCRecord] = []
    
    for rec in input_data.records:
        funding_usd = parse_funding_to_usd(rec.raw_funding_amount)
        std_batch = normalize_batch_format(rec.raw_batch)
        
        # Geographic Location Segmentation and Normalization
        loc_parts = [p.strip() for p in rec.raw_location.split(",") if p.strip()]
        city = loc_parts[0] if len(loc_parts) > 0 else "Unknown"
        country = loc_parts[-1] if len(loc_parts) > 1 else "USA"
        
        cleaned_list.append(
            NormalizedVCRecord(
                company_name=rec.raw_company_name.strip(),
                funding_usd=funding_usd,
                normalized_city=city,
                normalized_country=country,
                standard_batch=std_batch
            )
        )
        
    return NormalizerOutput(
        normalized_records=cleaned_list,
        total_processed=len(cleaned_list)
    )
