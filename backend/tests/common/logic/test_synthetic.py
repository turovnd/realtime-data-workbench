import json
from pathlib import Path

import pytest

from common.logic.synthetic import SAMPLES, synthetic_inputs


def test_demo_corpus_matches_the_independent_browser_preview() -> None:
    root = Path(__file__).resolve().parents[4]
    browser = json.loads((root / "frontend/src/api/demo/samples.json").read_text())
    assert [sample.model_dump() for sample in SAMPLES] == browser


def test_demo_batches_contain_24_distinct_customer_messages() -> None:
    records = synthetic_inputs("first", 12) + synthetic_inputs("second", 12, offset=12)
    assert len({record.text for record in records}) == 24
    assert len({record.identity for record in records}) == 24
    assert {record.channel for record in records} == {"Support", "In-app", "Community"}


@pytest.mark.parametrize("index", range(24))
def test_sample_takeaway_is_concise_and_grounded(index: int) -> None:
    sample = SAMPLES[index]
    assert len(sample.text) >= 250
    assert len(sample.analysis.summary) < len(sample.text) * 0.65
    assert sample.analysis.summary not in sample.text
    assert all(quote in sample.text for quote in sample.analysis.evidence)
