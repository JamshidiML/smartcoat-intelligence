# SmartCoat Engineering Baseline

Status: Release 1.7 baseline

Issue: #17

Branch: `thread/03-engineering-baseline-ci`

## Purpose

This document records the reproducible local development baseline for SmartCoat
Release 1.7 and explains which checks are currently ready to gate CI.

## Clean Python Environment

Validated interpreter:

```text
Python 3.12.13
```

Clean setup command:

```bash
python -m venv /private/tmp/smartcoat-1-7-threads/.venv312
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pip install -e '.[dev]'
```

The first install attempt in the restricted sandbox could not reach PyPI. The
same command succeeded when network access was allowed for dependency download.

## Declared Development Dependencies

The existing route tests import `fastapi.testclient.TestClient`. With the
current Starlette dependency, that import requires `httpx2`. Release 1.7 now
declares `httpx2>=2.7.0` in the `dev` optional dependency group so a clean
install can run the existing tests.

## Baseline Commands

Run these commands from the repository root after installing `.[dev]`:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

## Actual Baseline Results

| Check | Result | Notes |
|---|---:|---|
| `python -m pytest` | Pass | 13 tests passed after declaring `httpx2` for TestClient support. |
| `python -m ruff check .` | Fail | 24 existing findings: import formatting, line length, FastAPI `Depends` B008, and `datetime.UTC` modernization. |
| `python -m ruff format --check .` | Fail | `scripts/init_db.py` and `src/smartcoat/storage/database/models.py` would be reformatted. |
| `python -m mypy src` | Fail | 2 existing type errors in `EventService`, caused by `EventRepository.get/list` returning persistence records instead of `EnterpriseEvent`. |

## CI Gate for This Baseline

The CI workflow gates pull requests and relevant pushes on:

```bash
python -m pytest
```

Ruff and mypy are intentionally not enabled as required CI gates in this thread
because their failures are real baseline issues owned by other thread scopes,
especially Thread 04 for the event repository contract. They should become CI
gates after the owning fixes land and the baseline is re-measured.

## Local Development Notes

- Required Python version: 3.12 or newer.
- Do not commit `.env` files or secrets.
- Use `.env.example` only as a non-secret local-development template.
- Use synthetic or approved test data only.
- Run `git status` and `git diff --stat` before every commit.

## Follow-up Recommendations

1. Enable `python -m mypy src` as a CI gate after Thread 04 corrects the event
   repository return-type contract.
2. Enable `python -m ruff check .` after route dependency annotations and
   formatting findings are corrected in their owning scopes.
3. Enable `python -m ruff format --check .` after formatting is applied in the
   appropriate code-maintenance thread.
