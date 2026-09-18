# LLM Extraction Service

[![CI](https://github.com/evgenymu/llm-extraction-service/actions/workflows/ci.yml/badge.svg)](https://github.com/evgenymu/llm-extraction-service/actions/workflows/ci.yml)

An HTTP service that turns a job posting into validated, structured JSON using
a local language model.

**Status: works locally, not deployed.** Extraction runs against
[Ollama](https://ollama.com/) on the same machine. Accuracy has not been
measured yet — see *Known gaps* below.

## Why extraction

Extraction and classification are the most common production tasks built on
language models — far more common than chat. The output is either valid against
a schema or it is not, so correctness is checkable rather than a matter of taste.

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Ollama, with a model pulled: `ollama pull granite4.2:8b`

## Running it

```bash
cp .env.example .env          # LLM_MODEL has no default and must be set
uv sync
uv run uvicorn llm_extraction_service.main:app --reload
```

```bash
curl -s localhost:8000/extract -H 'Content-Type: application/json' \
  -d '{"text":"Senior Python Engineer, Warsaw, hybrid. 22 000 PLN/month."}'
```

Interactive docs: `http://127.0.0.1:8000/docs`

## Endpoints

| Endpoint | Purpose | Failure |
| --- | --- | --- |
| `GET /health` | Liveness: the process is up, and which build is serving. Touches no dependency, so a sick model cannot make a healthy process look dead | — |
| `GET /ready` | Readiness: the model server answers *and* has the configured model. Lists models, never generates text, and uses a short 2 s timeout so the probe fails fast | `503` |
| `POST /extract` | Extract one posting into a `JobPosting` | `502` model answered with an error or off-schema, `503` unreachable, `504` timeout |

Those status codes are deliberate. `500` would say "this service has a bug" and
wake someone up; `502`, `503` and `504` say the model server is at fault and are
safe for a client to retry.

## How it works

The pydantic schema is sent to Ollama as a decoding grammar, so the model can
only emit tokens that fit it — the answer is structurally valid by construction
rather than parsed out of prose afterwards.

Every field is required and nullable. A field the model may omit is a field it
can silently forget; a required field forces an explicit `null`, `unknown` or
`[]` instead.

Field descriptions do **not** reach the model through the schema: Ollama's
grammar ignores them (verified — identical output with and without them at
temperature 0). `extractor.build_prompt` renders them into the prompt, so the
descriptions stay the single source of truth for both the API docs and the
instructions the model actually reads.

## Known gaps

- **Accuracy is unmeasured.** The schema guarantees the *shape* of an answer,
  never its truth: a posting's salary can come back null, or a title can be
  merged with the company name, and every such answer still validates.
- **No retries or backoff.** A single timeout fails the request.
- **Net vs gross and contract type are not modelled**, which matters in Poland:
  25 000 net on B2B and 25 000 gross on an employment contract are very
  different offers.
- **Not deployed.** Ollama runs locally, so there is no public URL yet.
