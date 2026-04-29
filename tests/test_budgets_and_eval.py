from __future__ import annotations

from app.agents.chat import run_assessment_chat
from app.core.tokens import HANDOFF_CONTEXT_LIMIT
from app.eval.learning_loop import evaluate_prompt_version
from app.eval.scenarios import demo_borrower, seeded_scenarios


def test_handoff_stays_under_500_tokens() -> None:
    result = run_assessment_chat(demo_borrower(), seeded_scenarios()[0], "v2")
    assert result.token_counts["handoff_output"] <= HANDOFF_CONTEXT_LIMIT


def test_candidate_v2_beats_baseline() -> None:
    baseline = evaluate_prompt_version("baseline_v1", "eval_v2_compliance_gated")
    candidate = evaluate_prompt_version("candidate_v2", "eval_v2_compliance_gated")
    assert candidate.mean_score > baseline.mean_score
    assert candidate.compliance_pass_rate == 1.0
