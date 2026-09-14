"""HTTP entry point for the extraction service."""
import os,sys
from importlib.metadata import version

from fastapi import FastAPI
from pydantic import BaseModel

SERVICE_VERSION = version("llm-extraction-service")

app = FastAPI(
    title="LLM Extraction Service",
    description="Turn unstructured text into validated, structured JSON.",
    version=SERVICE_VERSION,
)


class Health(BaseModel):
    """Liveness response: the process is up, and this is the build serving it."""

    status: str
    version: str


@app.get("/health", tags=["ops"])
def health() -> Health:
    """Report that the process is alive and which build is answering.

    Deliberately shallow: it touches no dependency. A slow or failing
    downstream must not be able to make a healthy process look dead.
    """
    return Health(status="ok", version=SERVICE_VERSION)
