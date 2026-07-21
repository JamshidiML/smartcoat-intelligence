# T03 Engineering Baseline Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/17

Branch: `thread/03-engineering-baseline-ci`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/25

Final status: `100/100 — READY FOR APPROVAL`

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
- In the Cycle 4 candidate: `"$TMPDIR/smartcoat-cycle4-integration-venv/bin/python" -m pytest -q`
- In the Cycle 4 candidate: `"$TMPDIR/smartcoat-cycle4-integration-venv/bin/python" -m mypy src`
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
| Cycle 4 candidate full suite | PASS: 71 tests; 4 live tests skipped without opt-in | Candidate `8537f08` after T04 assembly. |
| Cycle 4 candidate MyPy | PASS: no issues in 44 source files | Candidate `8537f08` after T04 assembly. |
| GitHub Actions | PASS: run #8 for `f48b01d` | Exact current-head GitHub workflow evidence, conclusion success. |
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

- Exact current-head run #8 is recorded in PR #25; this report does not claim
  assembled-tree validation before the controlled candidate exists.
- Original snapshot environment/freeze command was not retained; this is documented provenance debt.
- Constraints are a Python 3.12 environment snapshot, not a universal hash lock.
- Ruff and formatting debt is owned by issue #36 and must reach zero before becoming CI gates.
- Candidate MyPy and the release-level suite pass after T04 assembly; final
  Cycle 4 review closed the integration-evidence correction.
- The 100/100 scope score does not mean Ruff/format debt is fixed and does not
  authorize production use, real-data ingestion, a merge to `main`, or later releases.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #25 current-head evidence deduction | 2 | RESOLVED | Cycle 3 reviewer confirmed current-head run #8 at `f48b01d`. |
| C02 | PR #25 constraints provenance deduction | 2 | RESOLVED | Cycle 3 reviewer confirmed honest provenance and regeneration limits. |
| C03 | PR #25 compatibility deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed Python 3.12 and non-universal lock limits. |
| C04 | PR #25 Cycle 3 integration-evidence deduction | 2 | RESOLVED | Final Cycle 4 review confirmed the 44-file MyPy pass, 71-test release suite, and successful candidate CI run #11; Ruff remains in issue #36. |
| C05 | PR #25 Ruff ownership deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed issue #36 owns repository-wide Ruff and format debt. |
| C06 | PR #25 report-contract deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed report-v2 and evidence traceability. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Final Cycle 4 review confirmed the current CI and assembled validation evidence. | None. |
| Scope and acceptance criteria | 20 | 20 | Owned and explicitly authorized files only. | None. |
| Architecture and North-Star alignment | 15 | 15 | Supports Release 1.7 engineering baseline. | None. |
| Verification, tests, or validation | 15 | 15 | Install, pip check, 71-test candidate suite, 44-file MyPy, and candidate CI passed. | None within issue #17 scope. |
| Security, privacy, and data governance | 10 | 10 | Least privilege, no secrets, and data-boundary checklist. | None. |
| Documentation and traceability | 10 | 10 | Baseline, issue, branch, PR, constraints, and report linked. | None. |
| Maintainability and clarity | 5 | 5 | CI is minimal, explicit, constrained, and documented with regeneration limits. | None. |
| Total | 100 | 100 | Final Cycle 4 review confirms completion within issue #17 scope. | None. |

## ChatGPT Reviewer Score

Reviewer total: 100

Reviewer evidence: GitHub PR #25 final Cycle 4 review submitted 2026-07-19, https://github.com/JamshidiML/smartcoat-intelligence/pull/25#pullrequestreview-4731489435.

## Final Score

Provisional weighted score: 100.0

Gate-adjusted score: 100.0

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
| 3 | 92 | Current CI evidence, provenance, compatibility, MyPy integration, Ruff ownership, and v2 migration required correction. | Recorded run #7, honest snapshot provenance, regeneration policy, compatibility limits, T04 cross-branch MyPy pass, issue #36, and v2 report. | 96 | Clean install, pip check, 13 tests, 24 Ruff findings, 2 format findings, 2 isolated T03 MyPy errors, T04 41-file MyPy pass, and run #7 success. | CLOSED |
| 4 | 98 | Cycle 3 reviewer closed branch findings and retained only assembled-tree MyPy and release-suite evidence. | Assembled T04, ran both checks, recorded exact results, and kept reviewer verification open without expanding Ruff scope. | 97 | Candidate `8537f08`: 71 passed, 4 opt-in live skips, and MyPy clean across 44 files. | CLOSED |
| 5 | 97.6 | Final Cycle 4 review confirmed assembled MyPy, release-suite, and candidate CI evidence. | Recorded final reviewer authority, resolved the integration item, normalized the scope-bounded self-score, and preserved issue #36. | 100 | PR #25 final Cycle 4 review and report-v2 validator pass. | CLOSED |

## Recommended Follow-up Issues

- Complete issue #36 and enable Ruff/format gates only when zero findings are demonstrated.
- Enable MyPy in CI only after integrated T04 contracts produce a green scoped result.

## Blockers

None.
