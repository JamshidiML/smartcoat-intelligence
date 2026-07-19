# SmartCoat Engineering Baseline

Status: Release 1.7 constrained working baseline

Issue: #17

Branch: `thread/03-engineering-baseline-ci`

## Purpose

This document records the constrained local development baseline for SmartCoat
Release 1.7 and explains which checks are currently ready to gate CI. The
committed constraints make the validated Python 3.12 dependency set repeatable;
they are not a cross-platform, hash-verified supply-chain lock.

## Clean Python Environment

Validated interpreter:

```text
Python 3.12.13
```

Clean setup command:

```bash
python -m venv .venv
.venv/bin/python -m pip install \
  --constraint requirements/constraints-py312.txt -e '.[dev]'
.venv/bin/python -m pip check
```

The constraints file pins the complete dependency set observed and validated
with Python 3.12. It is consumed as a constraint alongside the package metadata,
so editable installation still exercises the declared `.[dev]` dependencies.
Network access remains necessary when the pinned distributions are not cached.

Do not install the constraints file by itself: it intentionally does not replace
the project dependency declaration in `pyproject.toml`.

## Constraint Snapshot Provenance and Regeneration

`requirements/constraints-py312.txt` is a transitive package-version snapshot
captured on 2026-07-16 from the clean Python 3.12 environment used for Cycle 2.
The deleted temporary environment was not a durable artifact, and the exact
original freeze invocation was not retained. This provenance limitation is
recorded rather than reconstructed as false evidence.

Regenerate and review the snapshot deliberately:

1. Start from a clean supported Python 3.12 interpreter and empty virtual environment.
2. Install `-e '.[dev]'` without the old constraints to resolve a candidate set.
3. Run `python -m pip check`, the full test suite, Ruff, format check, and MyPy;
   record every pass and failure.
4. Capture `python -m pip freeze --exclude-editable` into a candidate constraints file.
5. Compare candidate versus committed versions. Review direct and transitive
   changes, release notes, security advisories, Python 3.12 support, and Linux CI
   availability; do not accept an unexplained bulk refresh.
6. Recreate a second empty environment and install the project using the
   candidate constraints. Rerun validation before replacing the committed file.
7. Record date, interpreter, platform, reviewer, reason, diff, and validation in
   the PR/report. Preserve the prior file in Git history.

The snapshot constrains versions validated on Python 3.12. It is neither a
hash-verified supply-chain lock nor proof of universal compatibility across
operating systems, CPU architectures, Python versions, or package indexes.

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
| Constrained clean install | Pass | Python 3.12 dependency set installed from `requirements/constraints-py312.txt`. |
| `python -m pip check` | Pass | Installed packages have compatible declared dependencies. |
| `python -m pytest` | Pass | 13 tests passed in 0.69 seconds in the Cycle 3 clean environment. |
| `python -m ruff check .` | Fail | 24 existing findings: import formatting, line length, FastAPI `Depends` B008, and `datetime.UTC` modernization. |
| `python -m ruff format --check .` | Fail | `scripts/init_db.py` and `src/smartcoat/storage/database/models.py` would be reformatted. |
| `python -m mypy src` | Fail | 2 event-service return errors on isolated T03; T04 commit `36eef25` passes all 41 source files, and the integration branch must be remeasured after merge. |

## CI Gate for This Baseline

The CI workflow gates pull requests and relevant pushes on:

```bash
python -m pip check
python -m pytest
```

Pull requests targeting `main` or `release/**` run once through the
`pull_request` event. Thread branches are intentionally excluded from `push`
events, preventing duplicate runs for an open thread PR. Direct pushes to
`main` and `release/**` remain covered. Workflow concurrency cancels superseded
runs for the same PR or branch.

Ruff, format, and MyPy are intentionally not required CI gates yet. Ownership
and enablement conditions are explicit:

- **MyPy owner:** T04 owns the event repository/service contract. Commit
  `36eef25` passes `python -m mypy src` for all 41 source files on the T04 branch.
  Enable MyPy only after that branch is integrated into the target baseline and
  `python -m mypy src` exits zero in a clean constrained environment.
- **Ruff route findings:** T04 owns the current FastAPI route dependency changes.
- **Remaining Ruff/format owner:** Release 1.8 engineering-quality
  [issue #36](https://github.com/JamshidiML/smartcoat-intelligence/issues/36)
  owns `scripts/init_db.py`,
  `src/smartcoat/agents/lab_agent.py`, `src/smartcoat/domain/base.py`, and
  `src/smartcoat/storage/database/models.py` rather than expanding T03 scope.
- **Enablement condition:** clean constrained runs of `ruff check .` and
  `ruff format --check .` both exit zero with no blanket suppressions; then add
  them to CI in the owning PR and demonstrate a successful Actions run.

The isolated T03 failures are measurements, not claims about the future
integrated branch. Rerun them after each owning correction lands.

## Local Development Notes

- Required Python version: 3.12 or newer.
- Use `requirements/constraints-py312.txt` for the validated Python 3.12 set.
- Review and regenerate constraints deliberately when dependencies change.
- Do not commit `.env` files or secrets.
- Use `.env.example` only as a non-secret local-development template.
- Use synthetic or approved test data only.
- Run `git status` and `git diff --stat` before every commit.

## Follow-up Recommendations

1. Remeasure `python -m mypy src` after T04 is integrated; enable only on zero errors.
2. Complete Release 1.8 Ruff/format debt issue #36 for the paths above.
3. Add Ruff/format gates only after zero-finding clean runs and successful CI.

## Current GitHub Actions Evidence

Commit `efa1c55addb55b347ba42a53a63b6cfc230417b5` completed SmartCoat CI run
`#7` successfully on 2026-07-19. This commit contains the schema-v2 report
migration. The final Cycle 3 commit/run pair is recorded in draft PR #25 after
push because a report cannot embed its own final commit hash without changing
that hash.
