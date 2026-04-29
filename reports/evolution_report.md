# Evolution Report

Seed: `20260429`
Learning-loop LLM spend: `$0.00` in this reproducible run. The implementation uses a deterministic simulator/judge for the submitted artifact; external LLM providers can be plugged in behind the same agent interface.

| Prompt version | Evaluator | Mean score | Compliance pass rate | Adopted | Decision |
| --- | --- | ---: | ---: | --- | --- |
| baseline_v1 | eval_v2_compliance_gated | 0.9133 | 1.0000 | False | Baseline control prompt. |
| candidate_v2 | eval_v2_compliance_gated | 0.9800 | 1.0000 | True | delta=0.0667, bootstrap_ci=[0.0400, 0.0867], compliance=1.00 |
| aggressive_candidate | eval_v2_compliance_gated | 0.6200 | 0.6667 | False | Rejected: compliance-gated evaluator found policy violations despite apparent outcome gains. |

## Statistical Test

Candidate v2 is compared against baseline v1 on the same seeded scenarios and stages.
Bootstrap 95% CI for mean score delta: `[0.04, 0.0867]`.
Adoption requires delta >= 0.05, lower CI > 0, and 100% compliance pass rate.

## Raw Data

Per-stage scores are in `reports/per_conversation_scores.csv`.
Machine-readable run data is in `data/runs/learning_loop_results.json`.
