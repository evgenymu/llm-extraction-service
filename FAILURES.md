# Failures

A running log of things that broke, how the break showed itself, and what it
taught. Entries marked *deliberate* were introduced on purpose to see how the
failure presents; the rest were real mistakes.

---

## 1. CI failed in six seconds: action tag did not exist

**Symptom.** The first CI run failed after 6 seconds, before any project code ran.

**How it was found.** The duration pointed at job setup rather than at lint or
tests. The log said:
`Unable to resolve action astral-sh/setup-uv@v10, unable to find version v10`.

**Cause.** The latest release was checked (`v10.1.0`) but the workflow used
`@v10`. `setup-uv` stopped publishing floating major tags after `v7`, so `v10`
does not exist as a ref.

**Fix.** Pin the exact tag: `astral-sh/setup-uv@v10.1.0`.

**Lesson.** A check has to match the exact claim being made. "The latest release
is v10.1.0" does not imply "`@v10` resolves". Also: read the run duration before
the log; a run that dies in seconds died in setup.

---

## 2. Green CI on dirty code (deliberate)

**Symptom.** A pull request with `import os,sys` (two unused imports on one line)
passed CI.

**How it was found.** Running `uv run ruff check .` locally reported the
violations the pipeline had not.

**Cause.** The `Lint` and `Check formatting` steps had been removed from
`ci.yml`. Nothing in the pipeline looked at style or unused imports any more.

**Fix.** Close the PR without merging; the gates on `main` were never removed.

**Lesson.** A pipeline catches exactly what it checks and nothing else. Green
means "the things we check are fine", not "the code is fine", and it looks
equally convincing either way.

---

## 3. NameError reported against the test file (deliberate)

**Symptom.** CI failed with
`ERROR tests/test_health.py - NameError: name 'app' is not defined`.

**How it was found.** The short summary names the test file, but the traceback
above it shows two frames: `tests/test_health.py:7` (the import) and then
`src/llm_extraction_service/main.py:24` (the decorator `@app.get`).

**Cause.** `app = FastAPI(...)` was renamed to `application` without updating the
decorator that still referenced `app`. The module failed at import time, so
pytest could not collect the test that imported it.

**Fix.** Close the PR without merging.

**Lesson.** The summary line names the victim; the last frame of the traceback
names the culprit. Read tracebacks from the bottom up. Stopping at the summary
would have sent the fix to a test that had nothing wrong with it.
