"""Tests for the prompt built from the schema. No model is involved."""

from llm_extraction_service.extractor import build_prompt
from llm_extraction_service.schema import JobPosting, Salary


def test_prompt_carries_every_field_description() -> None:
    """Descriptions never reach the model through the schema, only through here."""
    prompt = build_prompt("anything")

    for model in (JobPosting, Salary):
        for name, field in model.model_fields.items():
            assert field.description is not None, f"{name} has no description to send"
            assert field.description in prompt


def test_prompt_keeps_posting_text_verbatim() -> None:
    posting = 'Python dev. Config looks like {"debug": true} and {name}. Remote.'

    assert build_prompt(posting).endswith(posting)
