# Voice Project Intake Pilot Acceptance

Version: 1.0 Draft

Organization: `smartcoat-startup`

## Purpose

This three-day pilot demonstrates one bounded, human-reviewed path:

```text
voice, text, or Excel plus evidence
-> local transcription/import
-> local structured extraction Candidate
-> deterministic completeness questions
-> human correction and confirmation
-> governed Knowledge Object v2 draft
-> evidence/provenance-backed list and detail review
```

The Candidate is not canonical knowledge. Transcription, extraction, and import
must not write a Knowledge Object. Only the explicit human-confirm endpoint may
create a Knowledge Object v2 record, and that record begins in `draft`.

## Candidate Correlation IDs

`C-M-001`, `C-A-001`, and `C-S-001` are deterministic Candidate-local correlation
IDs. They connect materials, approaches, parameters, tests, samples, feedback, and
evidence during review; they are not source-system identifiers or asserted domain
facts. Optional `source_material_id`, `source_approach_id`, and `source_sample_id`
values are populated only when the source actually provides them. Generated
correlation IDs must never be presented as source evidence.

## Local Prerequisites

- Python 3.12 and the project development dependencies
- PostgreSQL using the existing SmartCoat development configuration
- Ollama listening only on `127.0.0.1` or `localhost`
- the configured Ollama model already downloaded locally
- Apple Silicon and the optional `pilot-voice` dependency for MLX Whisper
- browser microphone permission for voice capture

No CI job downloads speech or language models. CI uses deterministic fake
providers. No hosted AI provider is part of this pilot.

## Configuration

```text
SMARTCOAT_VOICE_TRANSCRIPTION_BACKEND=mlx_whisper
SMARTCOAT_WHISPER_MODEL=mlx-community/whisper-small-mlx
SMARTCOAT_OLLAMA_BASE_URL=http://127.0.0.1:11434
SMARTCOAT_OLLAMA_MODEL=qwen2.5:7b
SMARTCOAT_ASSET_ROOT=~/.local/share/smartcoat/pilot-assets
SMARTCOAT_MAX_UPLOAD_BYTES=26214400
```

The asset root is outside the repository. Never place confidential pilot assets,
audio, transcripts, workbooks, images, or generated model data in Git.

## Synthetic Demonstration Scenario

Use this exact synthetic statement:

> We received a request for a one-sided silicone-coated glass fabric for
> high-temperature flame protection. We tested three formulations. The first
> approach failed after the Bunsen test, but we did not record the exact coating
> weight. The second approach passed the laboratory flame test. We used
> magnesium hydroxide and calcium carbonate, cured at 210 degrees Celsius, and
> sent sample S-02 to the customer. We have not yet recorded the customer
> feedback or production feasibility.

The reviewed Candidate must contain or flag:

- the customer request and target application;
- a glass-fabric substrate;
- three approaches, or a warning that only two approaches were described clearly;
- magnesium hydroxide and calcium carbonate;
- a known curing temperature of `210 degC`;
- failed outcome for the first approach;
- explicit `not_measured` coating weight;
- passed result for the second approach;
- sample `S-02` marked as sent while retaining the missing sent date;
- pending customer feedback;
- production feasibility not assessed; and
- `human_confirmed=false`.

The deterministic completeness result must include at least:

1. What was the exact coating weight?
2. Why did approach C-A-001 fail?
3. Which test method and acceptance criteria were used?
4. When was sample S-02 sent?
5. Where is sample S-02 physically archived?
6. Has the customer provided feedback?
7. Was production feasibility evaluated?
8. Was price optimization evaluated?

## Demo Flow

1. Open `/lab-project-capture` on the local SmartCoat server.
2. Confirm the organization is `smartcoat-startup` and enter the pilot actor.
3. Run `/api/v2/lab-capture/preflight`; resolve local provider readiness failures.
4. Record the synthetic statement or submit it to `/api/v2/lab-capture/extract-text`.
5. Review the transcript, Candidate sections, completeness score, and questions.
6. Correct values and explicitly mark unknown, not measured, or not applicable fields.
7. Optionally upload a synthetic XLSX, PDF, or image evidence file.
8. Re-extract after adding answers if needed.
9. Verify voice re-extraction preserves the original transcript and `source_kind=voice`.
10. Verify original audio and transcript evidence are registered locally.
11. Verify the Candidate remains unconfirmed until the confirmation control is selected.
12. Confirm and submit to `/api/v2/lab-project-captures`.
13. Verify the returned object lifecycle is `draft`.
14. Verify the object in list/detail and inspect evidence, provenance, and audit behavior.

## Acceptance Gates

- Existing Lab Observation and QC Observation tests still pass.
- Candidate contracts reject blanks, invalid dates, invalid numeric measurements,
  extra fields, invented confirmation metadata, and oversized Knowledge Object content.
- Missing-information questions are deterministic.
- Local AI endpoints cannot write canonical knowledge.
- Excel import is dry-run Candidate generation only.
- Evidence storage is content-addressed, organization-partitioned, size-limited,
  and outside the repository.
- The canonical save requires explicit human confirmation and creates a draft through
  the existing governed audit service.
- Automated tests require no microphone, Ollama, MLX Whisper, or model download.

## Deliberate Pilot Boundaries

This pilot does not include production multi-tenancy, semantic search, embeddings,
RAG, pattern discovery, autonomous agents, hosted AI, ERP/LIMS integration, machine
control, full PDF OCR, or semantic TDS/SDS extraction. PDF and image scope is limited
to local evidence registration, integrity hashing, and Candidate references.

No implementation branch in this pilot may merge into Release 1.8 or `main` without
a separate independent review and explicit authorization.
