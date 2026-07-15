# Codex 10-Thread Master Launch Prompt

Copy the prompt below into a new Codex task connected to `JamshidiML/smartcoat-intelligence`.

---

## Prompt

You are the Lead Execution Orchestrator for SmartCoat Intelligence.

SmartCoat is a horizontal Enterprise Intelligence and Living Industry mother platform. Its North Star is to transform an industrial company or factory into a connected, learning, analyzing, recommending, decision-supporting, increasingly automated living system, while high-impact layers remain under explicit human governance and oversight.

Technical textiles are the first real proof domain with real industrial data. They are not the total market or the final platform boundary.

Knowledge Capture is one foundational vertical slice, not the definition of SmartCoat.

### Repository and Baseline

Repository:

`JamshidiML/smartcoat-intelligence`

Baseline and integration branch:

`release/1.7-project-reset`

Before doing any work, read:

1. `AGENTS.md`
2. `docs/strategy/SMARTCOAT_NORTH_STAR.md`
3. `docs/project/PROJECT_STATE.md`
4. `docs/project/PROJECT_HISTORY.md`
5. `docs/project/MVP_STRATEGY.md`
6. `docs/project/DECISION_LOG.md`
7. `docs/execution/EXECUTION_CONTROL_CENTER.md`
8. `SECURITY.md`
9. `CONTRIBUTING.md`
10. parent issue #14 and all assigned thread issues #15–#24

### Required Execution Mode

Delegate the ten independent workstreams below to ten specialized subagents and run them in parallel.

Maintain one logical thread per issue, one dedicated branch per thread, one owned file/subsystem boundary, one thread report, and one draft pull request.

Do not collapse the ten threads into one branch or one implementation.

Do not merge any pull request automatically.

Each branch must start from `release/1.7-project-reset`.

Each pull request must target `release/1.7-project-reset`.

If the runtime has a hard concurrency limit below ten, start the maximum number immediately and queue the remaining logical threads without combining their branches, scopes, reports, or PRs. Report the actual concurrency limit honestly.

### Ten Threads

#### Thread 01 — Issue #15

Living Industry North Star and Mother Platform model

Branch:

`thread/01-living-industry-north-star`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 02 — Issue #16

Root documentation, roadmap, changelog, and index synchronization

Branch:

`thread/02-documentation-synchronization`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 03 — Issue #17

Reproducible engineering baseline and CI

Branch:

`thread/03-engineering-baseline-ci`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 04 — Issue #18

Persistence and API contract audit and stabilization

Branch:

`thread/04-persistence-api-contracts`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 05 — Issue #19

Technical Textiles Canonical Schema v1

Branch:

`thread/05-technical-textile-canonical-schema`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 06 — Issue #20

Technical-textile data-source inventory and readiness matrix

Branch:

`thread/06-data-source-inventory-readiness`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 07 — Issue #21

Industrial data governance, confidentiality, consent, and human oversight

Branch:

`thread/07-data-governance-human-oversight`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 08 — Issue #22

Generic ingestion foundation prototype with provenance and validation

Branch:

`thread/08-ingestion-foundation-prototype`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 09 — Issue #23

Technical-textile living-factory pilot and investor/customer proof plan

Branch:

`thread/09-technical-textile-pilot-blueprint`

Read and follow the complete issue. Modify only its owned paths.

#### Thread 10 — Issue #24

Execution scorecards, correction loops, report templates, and validator

Branch:

`thread/10-execution-scorecards-loop`

Read and follow the complete issue. Modify only its owned paths.

### Global Thread Rules

For every thread:

1. Read the full assigned GitHub issue.
2. Inspect relevant repository sources before making claims.
3. Produce a short plan inside the thread activity before editing.
4. Stay inside the issue scope and owned paths.
5. If an external file must change, do not edit it. Record a cross-thread finding and recommend a follow-up issue.
6. Use synthetic, generalized, anonymized, or metadata-only examples.
7. Do not ingest or commit proprietary industrial data.
8. Do not commit customer data, supplier-confidential data, prices, formulas, internal emails, employee personal data, unpublished inventions, raw meeting recordings, credentials, secrets, or raw company datasets.
9. Do not redefine SmartCoat as only a voice agent, knowledge-capture app, textile-only product, generic chatbot, or formulation calculator.
10. Do not claim a test, command, validation, or result passed unless it was actually run.
11. Separate verified facts, inferences, proposals, assumptions, and open questions.
12. Preserve human oversight for high-impact, safety-critical, legal, strategic, irreversible, or high-uncertainty decisions.
13. Do not merge automatically.

### Quality Rubric — 100 Points

Every thread must self-score with evidence:

- Correctness and evidence: 25
- Scope and acceptance criteria: 20
- Architecture and North-Star alignment: 15
- Verification, tests, or validation: 15
- Security, privacy, and data governance: 10
- Documentation and traceability: 10
- Maintainability and clarity: 5

Total: 100

### Critical Gates

Any critical-gate failure means the thread cannot score above 79 until corrected:

- unverified claim presented as fact
- secret or confidential data committed
- unapproved product-identity or core-architecture change
- missing required tests or validation
- unsafe edit outside thread ownership
- acceptance criteria claimed complete while incomplete

### Required Improvement Loop

For each thread:

1. Implement the approved scope.
2. Run required tests or validation.
3. Produce the required thread report.
4. Complete the Codex self-score with evidence.
5. Open a draft PR targeting `release/1.7-project-reset`.
6. List every missing point as a numbered correction item.
7. Perform an internal second-pass review before handing the PR to ChatGPT.
8. Correct all issues found in the internal review.
9. Re-run validation.
10. Update the report, self-score, and correction-cycle history.

Do not falsely award 100/100. A self-score of 100 requires all acceptance criteria complete, all required validation executed, no critical-gate failure, and no unresolved in-scope defect.

ChatGPT will perform the independent reviewer score after the PRs are opened. Continue correction cycles on the same branches when review feedback is provided.

### Thread Report Requirements

Every report under `docs/execution/reports/` must include:

- thread ID and issue link
- branch and PR link
- objective
- files changed
- architecture impact
- security/data impact
- methods and commands executed
- actual results
- acceptance-criteria evidence
- Codex self-score by category
- critical-gate declaration
- known limitations
- lost points and correction items
- correction-cycle history
- recommended follow-up issues
- final status

Final status must be one of:

- `READY FOR CHATGPT REVIEW`
- `CORRECTION IN PROGRESS`
- `100/100 — READY FOR APPROVAL`
- `BLOCKED — HUMAN DECISION REQUIRED`

### Orchestrator Responsibilities

The main Codex thread must:

1. Monitor all ten subagent threads.
2. Prevent file-ownership overlap.
3. Surface blockers without silently changing scope.
4. Collect each thread's branch, PR, report, tests, self-score, and status.
5. Produce one final orchestration summary with a table containing:
   - thread ID
   - issue
   - branch
   - PR
   - status
   - files changed
   - validation result
   - Codex self-score
   - correction-cycle count
   - blockers
6. Do not merge.
7. End by telling the user that the next step is ChatGPT independent review and scoring of every PR.

### Start Now

Start all ten logical threads now.

First confirm:

- repository
- baseline branch
- parent control-center issue
- ten issue assignments
- ten branch names
- actual parallel concurrency available
- that no real industrial data will be ingested in this execution wave

Then begin execution without asking for additional clarification unless a genuine human decision is required by an issue.

---

## End Prompt
