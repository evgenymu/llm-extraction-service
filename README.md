# LLM Extraction Service

An HTTP service that turns unstructured text into validated, structured JSON
using a language model.

**Status: week 1 — skeleton only.** There is no model call yet. What exists is a
health endpoint, a test, and a CI pipeline. Extraction itself lands in week 2.

## Why extraction

Extraction and classification are the most common production tasks built on
language models — far more common than chat. The output is either valid against
a schema or it is not, so correctness is checkable rather than a matter of taste.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
