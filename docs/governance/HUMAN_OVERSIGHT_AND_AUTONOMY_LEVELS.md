# Human Oversight and Autonomy Levels

Status: Draft pilot control model

## Control Principle

Human oversight increases with impact, uncertainty, irreversibility, safety,
legal consequence, confidentiality, strategic importance, and scale. Model
confidence does not lower a required approval level. SmartCoat assistance must
remain attributable, reviewable, stoppable, and reversible.

## Levels

| Level | System role | Human control | Pilot examples |
|---|---|---|---|
| L0 Manual | Stores or displays approved facts | Human performs and records decision | View approved source record |
| L1 Assist | Extracts, summarizes, flags missing information | Human verifies every output before trust | Draft a knowledge object |
| L2 Recommend | Ranks options with evidence, uncertainty, and constraints | Authorized human chooses, rejects, or edits | Suggest prior lessons or a test plan |
| L3 Supervised Action | Executes a bounded, reversible, low-impact action after explicit approval | Human approves each action; monitoring and rollback required | Save an approved draft or send an internal review task |
| L4 Bounded Automation | Repeats pre-authorized, low-impact, reversible actions inside hard limits | Human owns policy, monitors exceptions, can stop; periodic reauthorization | Re-index already approved records |

No unrestricted or self-expanding autonomy is defined. L4 cannot approve data,
alter limits, broaden purpose, grant access, or promote its own outputs.

## Risk Assessment and Escalation

Assess each use for affected people/companies, safety, financial/contractual
impact, compliance, confidentiality, uncertainty, reversibility, time pressure,
scale, and detectability. Use the most restrictive result:

- low impact + reversible + bounded + monitored: up to L3/L4 after approval
- meaningful impact or uncertainty: L2 maximum
- high impact, safety/legal consequence, restricted data, or irreversibility:
  L1/L2 support only with explicit qualified-human decision
- unknown risk or failed control: L0 or disabled

## Decisions That Always Require Human Approval

- ingestion, purpose expansion, model training, external sharing, export, or deletion
- access to another organization, site compartment, or Restricted/Strategic data
- formulation/composition release, invention/patent action, or trade-secret disclosure
- customer/supplier commitments, pricing, contracting, purchasing, or payment
- product release, conformity/certification, quality disposition, recall, or safety action
- production parameter changes, machine actuation, maintenance safety, or shutdown
- employment evaluation, discipline, surveillance, voice/meeting capture, or personal-data rights
- regulatory/legal interpretation, incident notification, or waiver of controls
- changes to autonomy limits, approval policy, evidence threshold, or emergency-stop state

## Human Review Standard

The interface or record must show source/evidence, provenance, material
transformations, model/version, assumptions, uncertainty, conflicts, missing
information, permitted-use status, and proposed action. The reviewer records
identity/role, decision, rationale, corrections, timestamp, and scope. Silence,
timeout, or lack of correction is never approval.

Reviewers must be competent for the decision and free to reject. High-impact
reviews require an independent or second qualified reviewer where policy, law,
or the data owner requires it. Automation performance is monitored for error,
override, drift, disparate impact, near misses, and over-reliance.

## Failure, Incident, and Stop Behavior

On missing evidence, conflicting facts, permission mismatch, isolation failure,
unsafe recommendation, abnormal override rate, model/tool change, or monitoring
loss: prevent the action, preserve a minimal audit record, notify the responsible
human, and downgrade or disable automation. Emergency stop must block queued and
new actions, revoke affected credentials where appropriate, and require named
restart authority after verification.

## Pilot Limit

The first technical-textile pilot is capped at L2 for knowledge extraction and
recommendations, plus L3 only for saving an explicitly approved draft or routing
an internal review task. Production actuation, external communication, model
training, cross-company learning, and high-risk decisions are outside the pilot.

