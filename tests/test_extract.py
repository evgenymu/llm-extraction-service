"""Tests for /extract and /ready. No model server is involved.

Every test swaps the real extractor for a fake one, so the suite is fast,
deterministic and runs in CI where no model exists.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from llm_extraction_service.extractor import (
    ExtractionError,
    InvalidModelOutputError,
    ModelServerError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from llm_extraction_service.main import app, get_extractor
from llm_extraction_service.schema import JobPosting, Salary, Seniority, WorkMode

POSTING = JobPosting(
    title="ML Engineer",
    company=None,
    location="Warsaw",
    work_mode=WorkMode.REMOTE,
    seniority=[Seniority.MIDDLE, Seniority.SENIOR],
    salary=Salary(min=90000, max=110000, currency="EUR", period="year"),
    skills=["Python", "PyTorch"],
)


class FakeExtractor:
    """Answers with a fixed posting, a chosen failure, or "not ready"."""

    def __init__(self, *, error: ExtractionError | None = None, ready: bool = True) -> None:
        self._error = error
        self._ready = ready
        self.seen: list[str] = []

    @property
    def model_name(self) -> str:
        return "fake-model"

    def extract(self, text: str) -> JobPosting:
        self.seen.append(text)
        if self._error is not None:
            raise self._error
        return POSTING

    def is_ready(self) -> bool:
        return self._ready


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use(extractor: FakeExtractor) -> FakeExtractor:
    app.dependency_overrides[get_extractor] = lambda: extractor
    return extractor


def test_extract_returns_the_posting(client: TestClient) -> None:
    fake = use(FakeExtractor())

    response = client.post("/extract", json={"text": "ML Engineer, Warsaw, remote."})

    assert response.status_code == 200
    assert response.json() == POSTING.model_dump(mode="json")
    assert fake.seen == ["ML Engineer, Warsaw, remote."]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ModelUnavailableError("down"), 503),
        (ModelTimeoutError("too slow"), 504),
        (ModelServerError("upstream 404"), 502),
        (InvalidModelOutputError("not in schema"), 502),
    ],
)
def test_each_failure_maps_to_its_own_status(
    client: TestClient, error: ExtractionError, expected_status: int
) -> None:
    use(FakeExtractor(error=error))

    response = client.post("/extract", json={"text": "anything"})

    assert response.status_code == expected_status


def test_empty_text_is_rejected_before_the_model_is_called(client: TestClient) -> None:
    fake = use(FakeExtractor())

    response = client.post("/extract", json={"text": ""})

    assert response.status_code == 422
    assert fake.seen == []


def test_ready_reports_the_model_when_it_is_available(client: TestClient) -> None:
    use(FakeExtractor(ready=True))

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "model": "fake-model"}


def test_ready_fails_when_the_model_is_not_available(client: TestClient) -> None:
    use(FakeExtractor(ready=False))

    response = client.get("/ready")

    assert response.status_code == 503


def test_health_stays_up_while_the_model_is_down(client: TestClient) -> None:
    """Liveness must not depend on readiness, or a sick model kills the process."""
    use(FakeExtractor(error=ModelUnavailableError("down"), ready=False))

    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200
