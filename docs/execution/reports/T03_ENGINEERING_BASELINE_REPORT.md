# T03 Engineering Baseline Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/17

Branch: `thread/03-engineering-baseline-ci`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/25

Final status: `CORRECTION IN PROGRESS`

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

- `python -m pip install --constraint requirements/constraints-py312.txt -e '.[dev]'`
- `python -m pip check`
- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy src`
- `git diff --check`

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Python runtime | PASS: Python 3.12.13 | Clean Cycle 2 environment output. |
| Constrained install | PASS: fresh environment installed | Escalated Cycle 2 install output. |
| `pip check` | PASS: no broken requirements | Command output. |
| Pytest | PASS: 13 tests | Cycle 2 test output. |
| Ruff check | FAIL: 24 existing findings | Repository-wide measurement, not enabled as a gate. |
| Ruff format | FAIL: 2 files would be reformatted | Repository-wide measurement, not enabled as a gate. |
| MyPy | FAIL: 2 event-service return-type errors | Must be remeasured after T04 integration. |
| GitHub Actions | PASS: SmartCoat CI run #5 on older cited commit | Report correction must replace this with current run #6 evidence. |
| Owned-path check | PASS: six changed paths within T03 ownership/authorization | Branch diff against release baseline. |
| `git diff --check` | PASS: no whitespace errors | Cycle 2 command output. |

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

- Current-head/run evidence and constraints provenance need Cycle 3 correction.
- Constraints are a Python 3.12 environment snapshot, not a universal hash lock.
- Ruff and formatting debt need explicit ownership before becoming CI gates.
- MyPy must be remeasured after T04 contract changes are available.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #25 current-head evidence deduction | 2 | IN PROGRESS | Record current commit and GitHub Actions run #6. |
| C02 | PR #25 constraints provenance deduction | 2 | IN PROGRESS | Document generation, regeneration, review, and diff procedure. |
| C03 | PR #25 compatibility deduction | 1 | IN PROGRESS | State Python 3.12 snapshot and non-universal non-hash-lock limits. |
| C04 | PR #25 integrated MyPy deduction | 1 | IN PROGRESS | Remeasure after T04 integration and report actual current result. |
| C05 | PR #25 Ruff ownership deduction | 1 | IN PROGRESS | Name follow-up owner and CI-enablement acceptance condition. |
| C06 | PR #25 report-contract deduction | 1 | IN PROGRESS | Complete schema-v2 migration and final validation evidence. |

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
| 3 | 92 | Six Cycle 3 correction groups remain. | Schema-v2 normalization started; substantive validation continues in Wave C. | 96 | V2 structural validation pending this migration commit. | OPEN |

## Recommended Follow-up Issues

- Assign repository-wide Ruff/format debt and enable gates only when zero findings are demonstrated.
- Enable MyPy in CI only after integrated T04 contracts produce a green scoped result.

## Blockers

None.
