# 2-3 Minute Demo Video Script

## 0:00-0:20 - Intro

This is my Riverline collections-agent assignment. It implements one Temporal workflow per borrower, with three agents behind one borrower experience: assessment chat, resolution voice, and final notice chat.

## 0:20-0:50 - Architecture

Show `README.md` architecture diagram.

Key line to say:

The borrower experience is continuous, but internally Temporal executes three activities. Cross-modal continuity is handled by a structured handoff summary capped at 500 tokens.

## 0:50-1:25 - Run Demo

Run:

```bash
python scripts/run_demo.py
```

Point out:

- assessment chat verifies and gathers facts
- voice stage continues from chat without re-verification
- final notice references the prior call
- token counts are printed for each stage

## 1:25-2:05 - Evaluation

Run:

```bash
python scripts/rerun_eval.py
```

Open:

- `reports/evolution_report.md`
- `reports/per_conversation_scores.csv`

Key line to say:

Prompt v2 is adopted only because it improves mean score by 0.0667, the bootstrap confidence interval lower bound is above zero, and compliance pass rate is 100%.

## 2:05-2:35 - Meta-Evaluation

Open:

- `reports/meta_evaluation.md`

Key line to say:

The first evaluator was flawed because it allowed compliance failures to retain an acceptable aggregate score. The meta-evaluator corrected this by adding a hard compliance gate.

## 2:35-3:00 - Limitations

Key line to say:

For reproducibility and deadline risk, I used deterministic borrower and judge simulation and a transcript-level voice abstraction. A real LLM or voice provider can plug into the same agent boundary without changing Temporal, token budgeting, or evaluation.
