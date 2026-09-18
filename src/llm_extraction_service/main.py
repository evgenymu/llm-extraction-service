"""HTTP entry point for the extraction service."""

import logging
from functools import lru_cache
from importlib.metadata import version
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from llm_extraction_service.config import Settings
from llm_extraction_service.extractor import (
    ExtractionError,
    Extractor,
    InvalidModelOutputError,
    ModelServerError,
    ModelTimeoutError,
    ModelUnavailableError,
    OllamaExtractor,
)
from llm_extraction_service.schema import JobPosting

SERVICE_VERSION = version("llm-extraction-service")
MAX_POSTING_CHARS = 20_000

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Extraction Service",
    description="Turn unstructured text into validated, structured JSON.",
    version=SERVICE_VERSION,
)


@lru_cache
def get_extractor() -> Extractor:
    """Build the extractor once per process; tests override this dependency."""
    settings = Settings()
    return OllamaExtractor(
        model=settings.llm_model,
        host=settings.ollama_host,
        timeout_seconds=settings.llm_timeout_seconds,
    )


# Which failure belongs to whom. The distinction is not cosmetic: a 500 says
# "this service has a bug" and gets someone paged, while 502/503/504 say the
# model server is at fault and are safe for a client to retry.
STATUS_FOR_ERROR: dict[type[ExtractionError], int] = {
    ModelUnavailableError: 503,
    ModelTimeoutError: 504,
    ModelServerError: 502,
    InvalidModelOutputError: 502,
}


@app.exception_handler(ExtractionError)
def handle_extraction_error(request: Request, exc: ExtractionError) -> JSONResponse:
    status_code = STATUS_FOR_ERROR.get(type(exc), 500)
    logger.warning("extraction failed: %s: %s", type(exc).__name__, exc)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


class Health(BaseModel):
    """Liveness response: the process is up, and this is the build serving it."""

    status: str
    version: str


class Readiness(BaseModel):
    """Readiness response: the model this service needs is actually usable."""

    status: str
    model: str


class ExtractionRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=MAX_POSTING_CHARS,
        description="Raw job posting text.",
    )


@app.get("/health", tags=["ops"])
def health() -> Health:
    """Report that the process is alive and which build is answering.

    Deliberately shallow: it touches no dependency. A slow or failing
    downstream must not be able to make a healthy process look dead.
    """
    return Health(status="ok", version=SERVICE_VERSION)


@app.get("/ready", tags=["ops"])
def ready(extractor: Annotated[Extractor, Depends(get_extractor)]) -> Readiness:
    """Report whether this service can currently serve extraction requests.

    Unlike /health this does touch the model server, but only to list the
    models it has: no text is generated, so the check stays cheap and fast.
    """
    if not extractor.is_ready():
        raise HTTPException(status_code=503, detail="model server not ready")
    # Reported by the extractor, not read back from configuration: the point is
    # to show which model is actually serving, the same reason /health carries
    # the build version.
    return Readiness(status="ready", model=extractor.model_name)


@app.post("/extract", tags=["extraction"])
def extract(
    request: ExtractionRequest,
    extractor: Annotated[Extractor, Depends(get_extractor)],
) -> JobPosting:
    """Extract structured fields from one job posting.

    Fields the posting does not state come back as null, ``unknown`` or an
    empty list. The schema guarantees the shape of this answer, never its
    accuracy.
    """
    return extractor.extract(request.text)
