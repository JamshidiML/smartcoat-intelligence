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

1. Define 8-12 representative sanitized scenarios and their expected evidence.
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

## Exit Decision

Scale requires all critical guardrails pass, primary quality metrics do not
regress, at least one efficiency/retrieval metric improves by its pre-registered
threshold, and users/domain reviewers confirm practical value. Otherwise document
the result as learning, not success. Sponsor, Data Owner, Security, and domain
authority each retain a stop decision within their remit.

