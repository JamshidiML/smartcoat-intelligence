# T03 Engineering Baseline Report

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/17

Branch: `thread/03-engineering-baseline-ci`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/25

Final status: `CYCLE 2 IMPLEMENTED; INDEPENDENT RE-REVIEW REQUIRED`

## Objective

Establish a constrained Python 3.12 engineering baseline and add the first CI
quality gate without changing SmartCoat product behavior.

## Scope

Owned files changed:

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/development/ENGINEERING_BASELINE.md`
- `docs/execution/reports/T03_ENGINEERING_BASELINE_REPORT.md`
- `pyproject.toml`
- `requirements/constraints-py312.txt`

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
- Added committed Python 3.12 dependency constraints and used them in CI and
  documented local installation.
- Added explicit read-only workflow permissions, non-duplicating event
  coverage, superseded-run cancellation, and `pip check`.
- Added a pull request template with architecture, security, validation, and
  limitation prompts.
- Documented local setup commands, exact baseline results, and follow-up gates.

## Commands and Tests Executed

```bash
/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --version
/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m venv /private/tmp/smartcoat-1-7-threads/.venv312
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m pip install --constraint requirements/constraints-py312.txt -e '.[dev]'
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m pip check
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m pytest
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m ruff check .
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m ruff format --check .
/private/tmp/smartcoat-t03-cycle2-venv/bin/python -m mypy src
```

## Actual Results

| Command | Result |
|---|---|
| Python version | `Python 3.12.13` |
| Initial sandbox constrained install | Failed because restricted DNS could not reach PyPI build dependencies. |
| Escalated clean constrained install | Passed in a fresh Python 3.12.13 virtual environment. |
| `pip check` | Passed: `No broken requirements found.` |
| `pytest` before `httpx2` | Failed during collection because TestClient required `httpx2`. |
| `pytest` after `httpx2` | Passed: 13 tests passed. |
| `ruff check .` | Failed: 24 existing findings. |
| `ruff format --check .` | Failed: 2 files would be reformatted. |
| `mypy src` | Failed: 2 existing event-service return-type errors. |

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Clean install documented and tested | Constraints are committed and consumed by CI and local setup. |
| CI triggers on PRs and relevant pushes | `.github/workflows/ci.yml`. |
| CI uses Python 3.12 | `actions/setup-python@v5` with `python-version: "3.12"`. |
| Every enabled check has honest baseline result | `pip check` and pytest are enabled in CI and passed locally. |
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
- Constraints are Python 3.12 pins, not a hash-verified cross-platform lock.
- T03 does not correct code failures owned by T04 or future code-quality work.

## Cycle 1 Independent Review Findings

- Authoritative reviewer score: 92/100.
- Dependency resolution was broad and upgraded pip at runtime.
- Workflow permissions were implicit.
- Thread PR updates could trigger duplicate push and pull-request runs.
- Superseded workflow runs were not cancelled.
- Baseline wording overstated reproducibility without committed constraints.

## Cycle 2 Corrections

- Added `requirements/constraints-py312.txt` and removed runtime pip upgrades.
- Applied the constraints in CI and documented local installation.
- Added `permissions: contents: read`.
- Removed `thread/**` from push triggers while retaining PR coverage.
- Added workflow concurrency with `cancel-in-progress: true`.
- Added `python -m pip check` after dependency installation.
- Reframed the result as a constrained Python 3.12 working baseline.

## Lost Points and Correction Items

- Two points remain reserved for independent confirmation of the Cycle 2
  dependency and workflow changes.
- Two points remain deducted because repository-wide Ruff, formatting, and
  MyPy checks still have honestly reported failures on this isolated branch.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Actual command results recorded. | Independent Cycle 2 review is pending. |
| Scope and acceptance criteria | 20 | 20 | Owned files only; CI and docs complete. | None. |
| Architecture and North-Star alignment | 15 | 15 | Supports Release 1.7 engineering baseline. | None. |
| Verification, tests, or validation | 15 | 13 | Install and required checks executed. | Repository-wide non-pytest checks still fail on this branch. |
| Security, privacy, and data governance | 10 | 10 | No secrets; data-boundary PR checklist added. | None. |
| Documentation and traceability | 10 | 10 | Baseline doc and report link to issue. | None. |
| Maintainability and clarity | 5 | 4 | CI is minimal, explicit, and constrained. | Independent lock maintenance review is pending. |
| Total | 100 | 96 | Cycle 2 corrections are implemented locally. | Independent re-review remains required. |

## Critical-Gate Declaration

No critical gate failed within T03 scope. Existing ruff and mypy failures are
not claimed complete and are documented as deferred cross-thread work.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Changes Made | Ending Score |
|---:|---:|---|---|---:|
| 1 | 92 | Clean install lacked TestClient dependency. | Added `httpx2>=2.7.0` to dev dependencies. | 100 self-score; reviewer held 92. |
| 2 | 92 reviewer score | Unconstrained dependencies, implicit permissions, duplicate triggers, no cancellation, no `pip check`. | Added constraints, least privilege, event deduplication, concurrency cancellation, and dependency validation. | 96 provisional self-score; independent re-review pending. |

## Recommended Follow-up Issues

- Enable mypy in CI after Thread 04 fixes event repository return types.
- Enable ruff checks after owned route-formatting and lint findings are fixed.

## Blockers

No implementation blocker. Independent ChatGPT re-review is required before
the review loop can close.
