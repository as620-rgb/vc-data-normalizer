from types import SimpleNamespace
from verifier.task import verify_task


def test_verify_normalizer_gold():
    mock_agent_output = SimpleNamespace(
        normalized_records=[
            SimpleNamespace(
                company_name="Stripe",
                funding_usd=5500000.0,
                normalized_city="San Francisco",
                normalized_country="USA",
                standard_batch="SUMMER 2010"
            ),
            SimpleNamespace(
                company_name="DoorDash",
                funding_usd=2000000.0,
                normalized_city="San Francisco",
                normalized_country="USA",
                standard_batch="SUMMER 2013"
            )
        ],
        total_processed=2
    )

    result = verify_task(task_input={}, agent_output=mock_agent_output, workspace_path=".")
    assert result["score"] == 1.0


def test_verify_normalizer_broken():
    mock_broken_output = SimpleNamespace(
        normalized_records=[
            SimpleNamespace(
                company_name="Stripe",
                funding_usd="5.5 Million",  # Intentionally providing a string instead of a float
                normalized_city="SF",
                normalized_country="USA",
                standard_batch="W24"
            )
        ],
        total_processed=1
    )

    result = verify_task(task_input={}, agent_output=mock_broken_output, workspace_path=".")
    assert result["score"] == 0.0
