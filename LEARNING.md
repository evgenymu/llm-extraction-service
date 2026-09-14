# Learning notes

Written without looking at the code. Where I could not explain something yet,
it goes under "To revisit" instead of being papered over.

---

## Week 1 — project skeleton and CI

**What I built.** I created the skeleton of the project. It has one real test,
and CI runs the linter, the formatting check and the tests.

**What a green badge proves.** It proves that the code passes the linter, the
formatting check and one test. It does not prove the code is correct — only that
it passes what we check. It does not prove the service works when deployed
either: `TestClient` calls the app directly, without a real server.

**Reading a traceback.**

```
ERROR collecting tests/test_health.py
tests/test_health.py:7: in <module>
    from llm_extraction_service.main import app
src/llm_extraction_service/main.py:24: in <module>
    @app.get("/health", tags=["ops"])
E   NameError: name 'app' is not defined
```

The summary names `tests/test_health.py`, but that file only failed to import.
The last frame shows the cause: `main.py`, line 24. I can distinguish the
consequence from the cause.

### To revisit next week

- **Why does `/health` return the version?** My answer so far explains where the
  version comes from (package metadata, a single reliable source), but not why
  the endpoint needs to report it at all.
