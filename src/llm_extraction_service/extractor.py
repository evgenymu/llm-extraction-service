"""Turn posting text into a JobPosting with a language model."""

from typing import Protocol

import httpx
import ollama
from pydantic import BaseModel, ValidationError

from llm_extraction_service.schema import JobPosting, Salary

READINESS_TIMEOUT_SECONDS = 2.0


class ExtractionError(Exception):
    """Extraction did not produce a valid JobPosting."""


class ModelUnavailableError(ExtractionError):
    """The model server could not be reached."""


class ModelTimeoutError(ExtractionError):
    """The model server did not answer within the timeout."""


class ModelServerError(ExtractionError):
    """The model server answered with an error status."""


class InvalidModelOutputError(ExtractionError):
    """The model answered, but the answer does not match the schema."""


class Extractor(Protocol):
    @property
    def model_name(self) -> str:
        """Which model is actually in use, for the readiness report."""
        ...

    def extract(self, text: str) -> JobPosting: ...

    def is_ready(self) -> bool: ...


INSTRUCTIONS = """\
Extract the job posting below into the given JSON structure.

Extract every value the text states, as written. When the text does not state
something, use null, "unknown" or an empty list; never fill a gap with a guess.

Field guide:
"""


def _field_guide(model: type[BaseModel], prefix: str = "") -> list[str]:
    return [
        f"- {prefix}{name}: {field.description}"
        for name, field in model.model_fields.items()
        if field.description
    ]


def build_prompt(text: str) -> str:
    guide = _field_guide(JobPosting) + _field_guide(Salary, prefix="salary.")
    # The posting is concatenated, never made part of a format template.
    # "{text}".format(text=posting) would be safe too, but formatting a string
    # that already contains the posting raises KeyError on braces in the text.
    return INSTRUCTIONS + "\n".join(guide) + "\n\nJob posting:\n" + text


class OllamaExtractor:
    def __init__(self, model: str, host: str, timeout_seconds: float) -> None:
        self._model = model
        self._client = ollama.Client(host=host, timeout=timeout_seconds)
        # A readiness probe must answer fast; it never inherits the long
        # extraction timeout.
        self._probe = ollama.Client(host=host, timeout=READINESS_TIMEOUT_SECONDS)
        self._schema = JobPosting.model_json_schema()

    @property
    def model_name(self) -> str:
        return self._model

    def extract(self, text: str) -> JobPosting:
        try:
            response = self._client.chat(
                model=self._model,
                messages=[{"role": "user", "content": build_prompt(text)}],
                format=self._schema,
                options={"temperature": 0},
                think=False,
            )
        # The ollama client converts connection and HTTP errors, but lets
        # httpx timeouts through unchanged, so each is caught explicitly.
        except ConnectionError as e:
            raise ModelUnavailableError(str(e)) from e
        except httpx.TimeoutException as e:
            raise ModelTimeoutError("model server did not answer in time") from e
        except ollama.ResponseError as e:
            raise ModelServerError(f"model server returned {e.status_code}: {e.error}") from e

        try:
            return JobPosting.model_validate_json(response.message.content or "")
        except ValidationError as e:
            raise InvalidModelOutputError(str(e)) from e

    def is_ready(self) -> bool:
        """True when the server answers and the configured model is available."""
        try:
            available = self._probe.list().models
        except (ConnectionError, httpx.TimeoutException, ollama.ResponseError):
            return False
        return any(m.model == self._model for m in available)
