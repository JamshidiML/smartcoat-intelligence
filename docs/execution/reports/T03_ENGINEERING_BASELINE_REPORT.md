# T03 Engineering Baseline Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/17

Branch: `thread/03-engineering-baseline-ci`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/25

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Establish a constrained Python 3.12 engineering baseline and first CI quality
gate without changing SmartCoat product behavior.

## Files Changed

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/development/ENGINEERING_BASELINE.md`
- `pyproject.toml`
- `requirements/constraints-py312.txt`
- `docs/execution/reports/T03_ENGINEERING_BASELINE_REPORT.md`

All paths are owned by issue #17 or explicitly authorized by its review.

## Methods and Commands Executed

- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m pip install --constraint requirements/constraints-py312.txt -e '.[dev]'`
- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m pip check`
- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m pytest -q`
- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m ruff check .`
- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m ruff format --check .`
- `"$TMPDIR/smartcoat-cycle3-t03-venv/bin/python" -m mypy src`
- In the T04 worktree: `"$TMPDIR/smartcoat-cycle3-t04-venv/bin/python" -m mypy src`
- `git diff --check`

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Python runtime | PASS: Python 3.12.13 | Clean Cycle 3 environment output. |
| Constrained install | PASS: fresh Cycle 3 environment installed | Python 3.12.13 and committed constraints. |
| `pip check` | PASS: no broken requirements | Command output. |
| Pytest | PASS: 13 tests in 0.69 seconds | Final Cycle 3 test output. |
| Ruff check | FAIL: 24 existing findings | Repository-wide measurement, not enabled as a gate. |
| Ruff format | FAIL: 2 files would be reformatted | Repository-wide measurement, not enabled as a gate. |
| MyPy | FAIL: 2 event-service return-type errors | Must be remeasured after T04 integration. |
| T04 contract MyPy | PASS: no issues in 41 source files at `36eef25` | Cross-branch evidence; no integration or merge is claimed. |
| GitHub Actions | PASS: run #7 for `efa1c55` | GitHub commit workflow evidence, conclusion success. |
| Owned-path check | PASS: six changed paths within T03 ownership/authorization | Branch diff against release baseline. |
| `git diff --check` | PASS: no whitespace errors | Cycle 3 command output. |

## Acceptance-Criteria Evidence

- [x] Document and test a clean Python 3.12 installation.
  Evidence: committed constraints and clean constrained install.
- [x] Add pull-request and relevant-push CI triggers.
  Evidence: workflow events and non-duplicating thread behavior.
- [x] Use Python 3.12 and least privilege.
  Evidence: setup-python configuration and read-only contents permission.
- [x] Run only honest passing CI gates.
  Evidence: pip check and pytest are enabled; Ruff/MyPy remain measured debt.
- [x] Cancel superseded CI runs.
  Evidence: workflow concurrency and cancel-in-progress configuration.
- [x] Reinforce architecture, security, validation, and limitation review.
  Evidence: pull-request template prompts.
- [x] Avoid product behavior and confidential-data changes.
  Evidence: dependency/CI/docs-only paths and no secrets or data.

## Architecture Impact

No product or runtime architecture changed. CI supports the Release 1.7
issue-branch-PR-review operating model.

## Security and Data Impact

No industrial data, secrets, credentials, environment files, or datasets were
introduced. The workflow uses explicit read-only repository permissions.

## Known Limitations

- Final self-referential commit/run evidence must be recorded in PR #25 after push.
- Original snapshot environment/freeze command was not retained; this is documented provenance debt.
- Constraints are a Python 3.12 environment snapshot, not a universal hash lock.
- Ruff and formatting debt is owned by issue #36 and must reach zero before becoming CI gates.
- MyPy must be remeasured after T04 contract changes are available.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #25 current-head evidence deduction | 2 | IN PROGRESS | Run #7 for `efa1c55` recorded; final commit/run pair goes in PR #25 after push. |
| C02 | PR #25 constraints provenance deduction | 2 | IN PROGRESS | Honest snapshot origin and seven-step regeneration/review procedure documented. |
| C03 | PR #25 compatibility deduction | 1 | IN PROGRESS | Python 3.12 snapshot and platform/hash-lock limits are explicit. |
| C04 | PR #25 integrated MyPy deduction | 1 | IN PROGRESS | T04 `36eef25` passes 41 files; integration-branch remeasurement remains pending because merging is prohibited. |
| C05 | PR #25 Ruff ownership deduction | 1 | IN PROGRESS | Issue #36 owns named paths and zero-finding/CI acceptance criteria; re-review pending. |
| C06 | PR #25 report-contract deduction | 1 | IN PROGRESS | Schema-v2 validation passes; independent re-review pending. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Actual command results and CI behavior recorded. | Current run evidence correction remains. |
| Scope and acceptance criteria | 20 | 20 | Owned and explicitly authorized files only. | None. |
| Architecture and North-Star alignment | 15 | 15 | Supports Release 1.7 engineering baseline. | None. |
| Verification, tests, or validation | 15 | 13 | Install and required checks executed. | Repository-wide non-pytest checks are not yet green. |
| Security, privacy, and data governance | 10 | 10 | Least privilege, no secrets, and data-boundary checklist. | None. |
| Documentation and traceability | 10 | 10 | Baseline, issue, branch, PR, constraints, and report linked. | None. |
| Maintainability and clarity | 5 | 4 | CI is minimal, explicit, and constrained. | Constraints regeneration procedure remains. |
| Total | 100 | 96 | Cycle 2 implementation evidence. | Four self-score points remain. |

## ChatGPT Reviewer Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 23 | Reviewer confirmed constrained install and CI corrections. | Current head/run and provenance needed updates. |
| Scope and acceptance criteria | 20 | 20 | Scope remained compliant. | None. |
| Architecture and North-Star alignment | 15 | 15 | Engineering baseline aligned. | None. |
| Verification, tests, or validation | 15 | 13 | CI and pytest passed. | MyPy and Ruff integration evidence remained. |
| Security, privacy, and data governance | 10 | 10 | Least privilege correction confirmed. | None. |
| Documentation and traceability | 10 | 7 | Core baseline documented. | Constraints provenance and current evidence missing. |
| Maintainability and clarity | 5 | 4 | Constrained workflow is clear. | Regeneration ownership remained. |
| Total | 100 | 92 | GitHub PR #25 Cycle 2 review. | Eight reviewer points remain authoritative. |

## Final Score

Provisional weighted score: 93.6

Gate-adjusted score: 93.6

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Passing and failing checks are distinguished honestly. |
| G2 Confidential data | PASS | CI, dependency, and documentation artifacts only. |
| G3 Approved scope and architecture | PASS | Owned/authorized engineering paths only. |
| G4 Required validation | PASS | Required baseline validation ran; remaining checks are explicit debt. |
| G5 File ownership | PASS | Six changed paths are owned or review-authorized. |
| G6 Acceptance completeness | PASS | Every issue criterion is checked with evidence. |

Critical-gate result: PASS

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 92 | Clean install lacked TestClient dependency and deterministic controls. | Added dependency, constraints, least privilege, event deduplication, cancellation, and pip check. | 96 | Clean install, pip check, pytest, CI, and measured debt. | CLOSED |
| 2 | 96 | Reviewer required current evidence, constraint provenance, compatibility limits, integrated MyPy, Ruff ownership, and T10 migration. | Recorded 92 reviewer score and eight-point correction burden. | 92 | PR #25 Cycle 2 independent review. | CLOSED |
| 3 | 92 | Current CI evidence, provenance, compatibility, MyPy integration, Ruff ownership, and v2 migration required correction. | Recorded run #7, honest snapshot provenance, regeneration policy, compatibility limits, T04 cross-branch MyPy pass, issue #36, and v2 report. | 96 | Clean install, pip check, 13 tests, 24 Ruff findings, 2 format findings, 2 isolated T03 MyPy errors, T04 41-file MyPy pass, and run #7 success. | OPEN |

## Recommended Follow-up Issues

- Complete issue #36 and enable Ruff/format gates only when zero findings are demonstrated.
- Enable MyPy in CI only after integrated T04 contracts produce a green scoped result.

## Blockers

None.
