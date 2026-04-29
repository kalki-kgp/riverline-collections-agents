# Decision Journal Template

This file is only a drafting aid. The final decision journal should be handwritten, timestamped, photographed/scanned, and uploaded separately.

## Entry 1 - Python-Only System

Timestamp:

Options:
- TypeScript Temporal worker + Python eval
- Python-only implementation

Decision:
Python-only.

Reason:
I can explain Python more confidently live. Keeping API, Temporal worker, agents, and evaluation in one language reduces moving parts.

Tradeoff:
Temporal examples are more common in TypeScript, but the workflow is simple enough for Python.

## Entry 2 - Deterministic Evaluation Instead Of Live LLM Evaluation

Timestamp:

Options:
- Use live LLM borrower and judge calls
- Use deterministic seeded simulator and judge

Decision:
Use deterministic seeded simulator for the submitted reproducible artifact.

Reason:
The assignment requires reproducibility. Live LLM calls introduce nondeterminism, key failures, and cost variability. The architecture keeps a provider boundary so live LLMs can be added later.

Tradeoff:
Less realistic language variety, but stronger reproducibility and easier inspection.

## Entry 3 - Structured Handoff Instead Of Full Transcript

Timestamp:

Options:
- Pass full conversation transcript
- Pass paragraph summary
- Pass structured summary

Decision:
Structured summary.

Reason:
The 500-token handoff budget forces compression. Structured fields preserve operational facts: identity, hardship, offers, objections, do-not-contact state, and continuity notes.

Tradeoff:
May lose nuance, but avoids repeated questions and supports evaluation.

## Stuck Moment 1 - Python Packaging

Timestamp:

Problem:
Editable install failed because setuptools found multiple top-level folders.

Discovery:
The error showed `app`, `data`, and `reports` as accidental packages.

Recovery:
Added explicit setuptools package discovery for `app*` only.

## Stuck Moment 2 - Evaluation Bug

Timestamp:

Problem:
Initial scoring made valid assessment outputs score too low.

Discovery:
The judge compared the outcome to the entire expected-outcome map instead of the current stage’s expected outcome.

Recovery:
Fixed scorer to index expected outcome by stage.

## Intentionally Not Built

Timestamp:

Decision:
Did not integrate a live voice provider.

Reason:
The deadline made a fragile external integration risky. I built a transcript-producing voice boundary instead, which preserves the cross-modal handoff design and can be replaced by Vapi/Retell/Pipecat later.
