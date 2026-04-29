# Technical Writeup

## Architecture

The system is a single borrower pipeline orchestrated by Temporal. FastAPI receives borrower/demo requests, Temporal owns durable workflow state and retries, and three activities run the stage agents:

1. Assessment chat gathers facts and emits a structured handoff.
2. Resolution voice produces a call transcript and updates the handoff with offers, objections, and outcome.
3. Final notice chat gives the documented last offer and next steps.

The borrower sees one continuous experience because later agents receive structured summaries instead of starting from scratch.

## Cross-Modal Handoff

The handoff is a `HandoffSummary`, not an unstructured paragraph. It preserves fields the next agent must not lose: identity verification, financial situation, hardship flags, offers, objections, do-not-contact state, and continuity notes.

The summary is serialized to compact JSON and checked with `tiktoken`. If it exceeds 500 tokens, the run fails. Each agent also checks prompt plus handoff against the 2000-token total context limit.

## Self-Learning Approach

The submitted learning loop compares prompt versions on the same seeded borrower scenarios:

- cooperative
- combative
- evasive
- confused
- distressed/hardship

Each stage receives quantitative scores for task success, continuity, compliance, token efficiency, and borrower experience. Candidate prompt adoption requires:

- mean improvement of at least 0.05
- bootstrap 95% confidence interval lower bound above 0
- 100% compliance pass rate

This avoids adopting a prompt because one judge call “liked it.” The raw data is saved in `reports/per_conversation_scores.csv`.

## Meta-Evaluation

The meta-evaluation demonstrates a flawed primary evaluator that let compliance failures keep a deceptively acceptable aggregate score because task success was overweighted. The corrected evaluator applies a hard compliance gate: any policy violation makes that stage score 0. This catches the aggressive candidate and prevents adoption.

## Compliance

Compliance is checked after generated stage outputs:

- AI identity disclosure
- logging/recording disclosure
- no false criminal threats
- no harassment after stop-contact requests
- settlement offers within policy range
- hardship routing for sensitive situations
- professional language
- no full sensitive identifier leakage

Prompt candidates cannot be adopted unless compliance pass rate is 100%.

## Limitations

The submitted artifact uses deterministic simulation instead of live LLM calls so that Riverline can rerun the evaluation exactly. The voice stage is represented as a transcript-producing abstraction. A production build would add provider adapters for real LLMs and voice vendors, a larger scenario suite, human review for compliance edge cases, and real-time monitoring of deployed prompt drift.
