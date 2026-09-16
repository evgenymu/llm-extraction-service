"""Contract tests for the extraction schema. No model is involved."""

import pytest
from pydantic import ValidationError

from llm_extraction_service.schema import JobPosting, Seniority

VALID = {
    "title": "ML Engineer",
    "company": None,
    "location": "Warsaw",
    "work_mode": "remote",
    "seniority": ["middle", "senior"],
    "salary": {"min": 90000, "max": 110000, "currency": "EUR", "period": "year"},
    "skills": ["Python", "PyTorch"],
}


def test_accepts_a_seniority_range() -> None:
    posting = JobPosting.model_validate(VALID)

    assert posting.seniority == [Seniority.MIDDLE, Seniority.SENIOR]


@pytest.mark.parametrize("key", sorted(VALID))
def test_every_key_is_required(key: str) -> None:
    incomplete = {k: v for k, v in VALID.items() if k != key}

    with pytest.raises(ValidationError, match=key):
        JobPosting.model_validate(incomplete)


def test_rejects_fields_outside_the_schema() -> None:
    with pytest.raises(ValidationError):
        JobPosting.model_validate({**VALID, "benefits": ["gym"]})


def test_unknown_is_not_a_seniority_level() -> None:
    with pytest.raises(ValidationError):
        JobPosting.model_validate({**VALID, "seniority": ["unknown"]})


def test_schema_sent_to_the_model_requires_every_field() -> None:
    schema = JobPosting.model_json_schema()

    assert sorted(schema["required"]) == sorted(JobPosting.model_fields)
    assert schema["additionalProperties"] is False
