from __future__ import annotations

from app.agents.prompts import PROMPTS_V1, PROMPTS_V2
from app.agents.summarizer import summary_to_budgeted_text
from app.core.compliance import check_compliance, compliance_passed
from app.core.models import (
    AgentRunResult,
    AgentStage,
    BorrowerProfile,
    BorrowerScenario,
    Channel,
    HandoffSummary,
    Message,
)
from app.core.tokens import enforce_agent_context_budget


def run_assessment_chat(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    prompt_version: str = "v1",
) -> AgentRunResult:
    prompt = (PROMPTS_V2 if prompt_version == "v2" else PROMPTS_V1)[AgentStage.ASSESSMENT]
    messages = [
        Message(
            role="agent",
            content=(
                "I am an AI agent acting on behalf of Riverline Collections. "
                "This chat is logged. I need to verify the account ending "
                f"{borrower.partial_account_id} and understand your current ability to resolve it."
            ),
        ),
        Message(role="borrower", content=scenario.stated_position),
        Message(
            role="agent",
            content=_assessment_close(scenario),
        ),
    ]
    hardship_flags = ["hardship"] if scenario.expected_hardship else []
    if "medical" in scenario.financial_situation.lower():
        hardship_flags.append("medical")
    if "lost" in scenario.financial_situation.lower():
        hardship_flags.append("job_loss")

    summary = HandoffSummary(
        source_stage=AgentStage.ASSESSMENT,
        target_stage=AgentStage.RESOLUTION,
        identity_verified=True,
        borrower_position=scenario.stated_position,
        financial_situation=scenario.financial_situation,
        hardship_flags=sorted(set(hardship_flags)),
        objections=[] if scenario.behavior == "cooperative" else [scenario.behavior],
        do_not_contact=scenario.asks_to_stop_contact,
        continuity_notes=(
            "Identity verified via partial account. Do not re-verify. "
            "Continue from stated financial position."
        ),
    )
    summary_text, handoff_tokens = summary_to_budgeted_text(summary)
    token_counts = enforce_agent_context_budget(prompt.prompt, "")
    token_counts["handoff_output"] = handoff_tokens
    findings = check_compliance(messages, borrower)
    summary.compliance_flags = [finding.rule_id for finding in findings if not finding.passed]
    return AgentRunResult(
        stage=AgentStage.ASSESSMENT,
        channel=Channel.CHAT,
        messages=messages,
        outcome="situation_assessed" if compliance_passed(findings) else "compliance_failed",
        handoff_summary=summary,
        token_counts=token_counts,
        metadata={"prompt_version": prompt.version, "handoff_text": summary_text},
    )


def run_final_notice_chat(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    handoff: HandoffSummary,
    prompt_version: str = "v1",
) -> AgentRunResult:
    prompt = (PROMPTS_V2 if prompt_version == "v2" else PROMPTS_V1)[AgentStage.FINAL_NOTICE]
    handoff_text, handoff_tokens = summary_to_budgeted_text(handoff)
    amount = f"${borrower.amount_due_cents / 100:,.2f}"
    last_offer = handoff.offers_discussed[-1] if handoff.offers_discussed else "structured payment plan"
    if handoff.do_not_contact:
        agent_text = (
            "I am an AI agent acting on behalf of Riverline Collections. This chat is logged. "
            "Your stop-contact request has been acknowledged and the account is flagged. "
            "No further collection discussion will continue in this channel."
        )
        outcome = "flagged_do_not_contact"
    elif prompt_version == "v2":
        agent_text = (
            "I am an AI agent acting on behalf of Riverline Collections. This chat is logged. "
            f"Following the call, the remaining balance is {amount}. The last available option is "
            f"{last_offer}, expiring in 48 hours. If unresolved, documented next steps are "
            "credit reporting, legal referral review, and asset recovery review. "
            "If hardship still applies, hardship-program review remains available."
        )
        outcome = "resolved" if scenario.likely_resolution != "no_deal" else "flag_for_review"
    else:
        agent_text = (
            "I am an AI agent acting on behalf of Riverline Collections. This chat is logged. "
            f"The remaining balance is {amount}. The last available option is {last_offer}, "
            "expiring in 48 hours. If unresolved, documented next steps are credit reporting, "
            "legal referral review, and asset recovery review."
        )
        outcome = "resolved" if scenario.likely_resolution != "no_deal" else "flag_for_review"

    messages = [
        Message(role="agent", content=agent_text),
        Message(
            role="borrower",
            content="I understand." if outcome == "resolved" else "I cannot commit to anything.",
        ),
    ]
    token_counts = enforce_agent_context_budget(prompt.prompt, handoff_text)
    token_counts["handoff_input"] = handoff_tokens
    findings = check_compliance(messages, borrower)
    return AgentRunResult(
        stage=AgentStage.FINAL_NOTICE,
        channel=Channel.CHAT,
        messages=messages,
        outcome=outcome if compliance_passed(findings) else "compliance_failed",
        token_counts=token_counts,
        metadata={
            "prompt_version": prompt.version,
            "handoff_text": handoff_text,
            "compliance_findings": [finding.model_dump() for finding in findings],
        },
    )


def _assessment_close(scenario: BorrowerScenario) -> str:
    if scenario.asks_to_stop_contact:
        return "Your request to stop contact is acknowledged. I will flag the account."
    if scenario.expected_hardship:
        return (
            "I have recorded the financial hardship information. A hardship-program path "
            "must be considered before any standard resolution pressure."
        )
    return "I have recorded your current financial position. The next step is resolution options."
