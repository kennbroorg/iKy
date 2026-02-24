# Unit Tests for iKy Python Backend

**Date:** 2026-02-24
**Status:** Approved

## Goal

Add unit tests to the Python backend, runnable inside the Docker container via `just test`.

## Approach

Approach B: proper pytest with fixtures. Tests run inside the existing backend container (which has Redis available), using `docker compose exec`.

## Files to Create/Modify

| File | Action |
|------|--------|
| `requirements.txt` | Add `pytest` |
| `backend/pyproject.toml` | pytest config (testpaths, pythonpath) |
| `backend/tests/__init__.py` | Empty package marker |
| `backend/tests/conftest.py` | Flask test client fixture, Celery send_task mock |
| `backend/tests/test_iky_functions.py` | Tests for all pure functions in iKy_functions.py |
| `backend/tests/test_api.py` | Tests for API endpoints (mock Celery dispatch) |
| `backend/tests/test_github_tasks.py` | Tests for p_github processing (mock HTTP) |
| `justfile` | Add `test` recipe |

## Fixtures (conftest.py)

- **`app`** - Flask app via `create_application()`, `TESTING=True`
- **`client`** - Flask test client
- **`mock_celery_send`** - Patches `celery.send_task` returning mock AsyncResult

## Test Coverage

### test_iky_functions.py (~40 cases)

All pure functions: `extract_hashtags`, `extract_mentions`, `extract_url`, `extract_mails`, `extract_url_*`, `extract_*`, `analize_rrss`, `name_match`, `simple_analysis`, `deep_analysis`.

### test_api.py (~10 cases)

Representative POST endpoints verify correct Celery task dispatch and response shape. GET endpoints (`/tasklist`, `/testing`).

### test_github_tasks.py (~5 cases)

Mock `requests.get` with fixture JSON. Test `p_github` output structure, email extraction, error handling, validation flag.

## Running

```
just test              # all tests
just test -k functions # filter by keyword
```

Maps to: `docker compose exec backend pytest -v`
