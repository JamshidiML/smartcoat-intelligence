# T03 Engineering Baseline Report

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/17

Branch: `thread/03-engineering-baseline-ci`

Draft PR: Pending

Final status: `READY FOR CHATGPT REVIEW`

## Objective

Establish a reproducible Python 3.12 engineering baseline and add the first CI
quality gate without changing SmartCoat product behavior.

## Scope

Owned files changed:

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/development/ENGINEERING_BASELINE.md`
- `docs/execution/reports/T03_ENGINEERING_BASELINE_REPORT.md`
- `pyproject.toml`

## Inputs Reviewed

- `AGENTS.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/project/PROJECT_STATE.md`
- `docs/project/MVP_STRATEGY.md`
- `docs/project/DECISION_LOG.md`
- `docs/execution/EXECUTION_CONTROL_CENTER.md`
- Issue #17
- Existing `pyproject.toml`
- Existing tests under `tests/`

## Execution Plan

1. Create a clean Python 3.12 environment.
2. Install the project with `.[dev]`.
3. Run pytest, ruff, ruff format check, and mypy.
4. Gate CI only on checks that have an honest passing baseline.
5. Record failures as deferred follow-up items instead of hiding them.

## Work Completed

- Added the missing `httpx2` dev dependency required by Starlette TestClient.
- Added GitHub Actions CI for Python 3.12 pytest.
- Added a pull request template with architecture, security, validation, and
  limitation prompts.
- Documented local setup commands, exact baseline results, and follow-up gates.

## Commands and Tests Executed

```bash
/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --version
/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m venv /private/tmp/smartcoat-1-7-threads/.venv312
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pip install -e '.[dev]'
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pytest
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m ruff check .
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m ruff format --check .
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m mypy src
```

## Actual Results

| Command | Result |
|---|---|
| Python version | `Python 3.12.13` |
| Initial sandbox install | Failed because restricted DNS could not reach PyPI. |
| Escalated install | Passed. |
| `pytest` before `httpx2` | Failed during collection because TestClient required `httpx2`. |
| `pytest` after `httpx2` | Passed: 13 tests passed. |
| `ruff check .` | Failed: 24 existing findings. |
| `ruff format --check .` | Failed: 2 files would be reformatted. |
| `mypy src` | Failed: 2 existing event-service return-type errors. |

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Clean install documented and tested | `docs/development/ENGINEERING_BASELINE.md`; install succeeded in Python 3.12 venv. |
| CI triggers on PRs and relevant pushes | `.github/workflows/ci.yml`. |
| CI uses Python 3.12 | `actions/setup-python@v5` with `python-version: "3.12"`. |
| Every enabled check has honest baseline result | Pytest is the only enabled CI gate and passed locally. |
| Existing failures fixed only within owned paths or documented | Only `pyproject.toml` changed; ruff/mypy failures documented. |
| No application behavior changed | Only dependency metadata, CI, PR template, and docs changed. |
| PR template reinforces workflow | `.github/pull_request_template.md`. |
| No secrets embedded | Workflow uses no secrets or credentials. |

## Architecture Impact

No product or runtime architecture changed. The CI workflow supports the
Release 1.7 issue -> branch -> PR -> review operating model.

## Security and Data Impact

No confidential industrial data, secrets, credentials, `.env` files, or raw
datasets were introduced. The PR template adds a data-boundary checkbox.

## Known Limitations

- Ruff and mypy are measured but not yet gating CI.
- The first clean install requires network access to download dependencies.
- T03 does not correct code failures owned by T04 or future code-quality work.

## Lost Points and Correction Items

No in-scope deductions remain after adding `httpx2` and documenting the
non-gated checks. Out-of-scope baseline failures remain as follow-ups.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Actual command results recorded. | None. |
| Scope and acceptance criteria | 20 | 20 | Owned files only; CI and docs complete. | None. |
| Architecture and North-Star alignment | 15 | 15 | Supports Release 1.7 engineering baseline. | None. |
| Verification, tests, or validation | 15 | 15 | Install and required checks executed. | None. |
| Security, privacy, and data governance | 10 | 10 | No secrets; data-boundary PR checklist added. | None. |
| Documentation and traceability | 10 | 10 | Baseline doc and report link to issue. | None. |
| Maintainability and clarity | 5 | 5 | CI is minimal and explicit. | None. |
| Total | 100 | 100 | All in-scope acceptance criteria are met. | None. |

## Critical-Gate Declaration

No critical gate failed within T03 scope. Existing ruff and mypy failures are
not claimed complete and are documented as deferred cross-thread work.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Changes Made | Ending Score |
|---:|---:|---|---|---:|
| 1 | 92 | Clean install lacked TestClient dependency. | Added `httpx2>=2.7.0` to dev dependencies. | 100 |

## Recommended Follow-up Issues

- Enable mypy in CI after Thread 04 fixes event repository return types.
- Enable ruff checks after owned route-formatting and lint findings are fixed.

## Blockers

None for this thread.
