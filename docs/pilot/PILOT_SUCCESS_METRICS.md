# Pilot Success Metrics

Status: Measurement protocol; targets require sponsor approval after baseline

## Measurement Rules

- Pre-register scenarios, definitions, exclusions, target thresholds, sample size,
  and analysis before assisted results are opened.
- Measure baseline and assisted workflows on comparable sanitized scenarios,
  stratified by user role and task complexity.
- Report medians and distributions, denominators, missing observations, errors,
  and confidence intervals where sample size supports them; do not cherry-pick.
- Separate system telemetry, rubric scoring, reviewer judgment, and interviews.
- Never trade quality, governance, safety, or user burden for speed.

## Primary Metrics

| Metric | Operational definition | Collection | Decision threshold |
|---|---|---|---|
| Capture completeness | Required critical fields present and valid / required critical fields for scenario | Blinded rubric review of baseline and assisted records | Sponsor pre-registers improvement; no critical-field regression |
| Major correction rate | Approved drafts needing meaning-changing correction / reviewed drafts | Field-level review log | Must remain below pre-registered ceiling |
| Evidence/provenance coverage | Approved claims with valid evidence and source/actor/time/method / approved claims | Record audit | No decrease; critical claims require full coverage |
| Capture cycle time | Minutes from task start to approved or explicitly deferred record | Timestamped observation | Material median reduction without quality loss |
| Retrieval success | Tasks where user finds at least one judged-useful reviewed record / retrieval tasks | Scenario result and relevance judgment | Material improvement over baseline |
| Context reconstruction time | Minutes to answer the pre-defined project-context questions with cited evidence | Timed scenario | Material median reduction without accuracy loss |
| Lesson reuse | Later decisions where a reviewed prior lesson is cited and judged influential / eligible decisions | Decision record plus human confirmation | Positive, auditable reuse signal |

Numeric improvement thresholds are intentionally blank until G0 baseline design;
recording aspirational numbers now would manufacture evidence.

## Guardrail Metrics

| Guardrail | Definition | Critical response |
|---|---|---|
| Permission/isolation breach | Any unauthorized purpose, principal, processor, site, or company exposure | Stop pilot and incident process; target zero |
| Unreviewed promotion | Draft/AI output presented as approved knowledge | Block and correct; target zero |
| Unsupported critical claim | Safety, quality, customer, or technical conclusion without required evidence | Reject promotion; target zero |
| Material factual error | Reviewer finds output could change a technical decision | Record, analyze, and apply pre-set stop ceiling |
| Deletion/stop failure | Approved deletion or emergency stop cannot be verified | No live pilot |
| User burden | Extra minutes, questions, duplicate entry, or workflow abandonment | Investigate by task and role |

## Pre-Registered Stop and Pause Rules

Numeric ceilings are approved at G0 after baseline measurement; leaving the
numbers open here does not leave the response undefined.

| Trigger | Pre-registration requirement | Mandatory response |
|---|---|---|
| Unacceptable correction rate | Define meaning-changing correction ceiling, observation window, and critical-field weighting before assisted results are opened | Pause assisted capture when the ceiling is crossed; review affected records and root cause before restart |
| Retrieval failure | Define no-useful-result ceiling, required-result set where knowable, and harmful/unsupported-result severity | Pause retrieval claims and workflow expansion when the ceiling is crossed; a harmful unsupported critical result can stop immediately |
| Confidentiality, purpose, or tenant incident | Target is zero; incident owner and containment route approved before access | Stop live use immediately, contain access, preserve audit evidence, notify the owner, and require explicit restart approval |
| Weak baseline comparability | Pre-register scenario matching, role/task strata, timing convention, completion rubric, exclusions, and minimum comparable sample | Do not calculate an improvement claim; pause or repeat baseline/assisted collection rather than substitute unmatched observations |
| Unreviewed promotion or deletion/stop failure | Target is zero and synthetic rehearsal must exercise both controls | Stop the pilot; no live restart until correction and independent verification |

The stop owner may act within their remit without waiting for a group vote.
Crossing a pause threshold is recorded as evidence and cannot be removed by
changing the metric definition after results are visible.

## Secondary and Qualitative Evidence

- field-level correction pattern and missing-information usefulness
- retrieval precision at the selected result count and reasons for rejection
- reviewer agreement on fact/observation/hypothesis/recommendation labels
- System Usability Scale or pre-selected short instrument, reported honestly
- structured interviews: trust, evidence clarity, workflow fit, adoption barriers,
  surprising value, and reasons for non-use
- number and quality of repeated-failure or duplicate-work cases identified;
  do not claim avoidance without a documented counterfactual decision

## Study Design

1. Sponsor and Data Owner approve the planning assumption of 8-12 representative
   sanitized scenarios, or replace it with a justified feasible count, and define
   expected evidence.
2. Observe each participant on baseline tasks before training on assisted flow.
3. Run synthetic rehearsal and calibrate rubric reviewers.
4. Collect assisted tasks over the operational period; label practice tasks.
5. Sample records for independent domain/quality review; reconcile disagreements.
6. Analyze by metric and guardrail, including failures and missing data.
7. Decide `stop`, `iterate`, `repeat`, or `scale` using pre-registered rules.

## Evidence Record

For every reported metric retain: metric version, scenario/cohort, numerator,
denominator, raw event references, exclusions and reasons, calculation code or
method, reviewer, date, result, uncertainty, guardrail status, and claim ID. Use
only sanitized summaries in investor/customer material.

An effect that misses its pre-registered threshold, has an insufficient
comparable sample, or fails a guardrail is reported as unsupported or
inconclusive. It cannot be upgraded by a testimonial, a post-hoc metric, or a
different denominator.

## Exit Decision

Scale requires all critical guardrails pass, primary quality metrics do not
regress, at least one efficiency/retrieval metric improves by its pre-registered
threshold, and users/domain reviewers confirm practical value. Otherwise document
the result as learning, not success. Sponsor, Data Owner, Security, and domain
authority each retain a stop decision within their remit.
