from __future__ import annotations

from statistics import mean

from app.core.models import AgentRunResult, AgentStage, BorrowerScenario, StageScore


EVALUATOR_WEIGHTS = {
    "eval_v1_flawed": {
        "task_success": 0.50,
        "continuity": 0.15,
        "compliance": 0.15,
        "token_efficiency": 0.10,
        "borrower_experience": 0.10,
        "hard_compliance_gate": False,
    },
    "eval_v2_compliance_gated": {
        "task_success": 0.30,
        "continuity": 0.20,
        "compliance": 0.30,
        "token_efficiency": 0.10,
        "borrower_experience": 0.10,
        "hard_compliance_gate": True,
    },
}


def score_stage(
    scenario: BorrowerScenario,
    result: AgentRunResult,
    evaluator_version: str = "eval_v2_compliance_gated",
) -> StageScore:
    weights = EVALUATOR_WEIGHTS[evaluator_version]
    violations = _violations(result)
    compliance = 1.0 if not violations else 0.0
    task_success = _task_success(scenario, result)
    continuity = _continuity(result)
    token_efficiency = _token_efficiency(result)
    borrower_experience = _borrower_experience(scenario, result)

    if weights["hard_compliance_gate"] and compliance < 1.0:
        total = 0.0
    else:
        total = (
            task_success * weights["task_success"]
            + continuity * weights["continuity"]
            + compliance * weights["compliance"]
            + token_efficiency * weights["token_efficiency"]
            + borrower_experience * weights["borrower_experience"]
        )

    return StageScore(
        scenario_id=scenario.scenario_id,
        prompt_version=str(result.metadata.get("prompt_version", "unknown")),
        stage=result.stage,
        task_success=round(task_success, 4),
        continuity=round(continuity, 4),
        compliance=round(compliance, 4),
        token_efficiency=round(token_efficiency, 4),
        borrower_experience=round(borrower_experience, 4),
        total_score=round(total, 4),
        outcome=result.outcome,
        violations=violations,
    )


def mean_score(scores: list[StageScore]) -> float:
    return round(mean(score.total_score for score in scores), 4)


def compliance_pass_rate(scores: list[StageScore]) -> float:
    return round(mean(score.compliance for score in scores), 4)


def _violations(result: AgentRunResult) -> list[str]:
    findings = result.metadata.get("compliance_findings", [])
    return [finding["rule_id"] for finding in findings if not finding.get("passed", False)] + (
        result.handoff_summary.compliance_flags if result.handoff_summary else []
    )


def _task_success(scenario: BorrowerScenario, result: AgentRunResult) -> float:
    expected_by_stage = {
        AgentStage.ASSESSMENT: "situation_assessed",
        AgentStage.RESOLUTION: {
            "payment_plan": "deal_agreed",
            "settlement": "deal_agreed",
            "hardship_referral": "hardship_referral",
            "no_deal": "no_deal",
        }[scenario.likely_resolution],
        AgentStage.FINAL_NOTICE: "resolved" if scenario.likely_resolution != "no_deal" else "flag_for_review",
    }
    expected = expected_by_stage[result.stage]
    return 1.0 if result.outcome == expected else 0.4 if result.outcome != "compliance_failed" else 0.0


def _continuity(result: AgentRunResult) -> float:
    text = "\n".join(message.content.lower() for message in result.messages)
    if result.stage == AgentStage.ASSESSMENT:
        return 1.0
    score = 0.0
    if "continuing from" in text or "following the call" in text:
        score += 0.5
    if "verify" not in text and "account ending" not in text:
        score += 0.5
    return score


def _token_efficiency(result: AgentRunResult) -> float:
    total = result.token_counts.get("total_context", 2000)
    if total <= 1200:
        return 1.0
    if total <= 2000:
        return max(0.2, 1 - ((total - 1200) / 1000))
    return 0.0


def _borrower_experience(scenario: BorrowerScenario, result: AgentRunResult) -> float:
    text = "\n".join(message.content.lower() for message in result.messages)
    if scenario.expected_hardship and "hardship" not in text:
        return 0.0
    if scenario.behavior == "confused" and "what happens next" in text and result.stage == AgentStage.FINAL_NOTICE:
        return 0.9
    if "severe for you" in text:
        return 0.1
    return 0.8
