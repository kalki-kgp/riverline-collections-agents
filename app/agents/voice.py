from __future__ import annotations

from pathlib import Path

from app.agents.prompts import AGGRESSIVE_PROMPTS, PROMPTS_V1, PROMPTS_V2
from app.agents.summarizer import merge_handoffs, summary_to_budgeted_text, transcript_text
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
from app.core.store import REPORTS_DIR, ensure_dirs, utc_timestamp
from app.core.tokens import enforce_agent_context_budget


def run_resolution_voice(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    handoff: HandoffSummary,
    prompt_version: str = "v1",
) -> AgentRunResult:
    prompts = PROMPTS_V2 if prompt_version == "v2" else PROMPTS_V1
    if prompt_version == "aggressive":
        prompts = AGGRESSIVE_PROMPTS
    prompt = prompts[AgentStage.RESOLUTION]
    handoff_text, handoff_tokens = summary_to_budgeted_text(handoff)
    discount = _discount_for_scenario(scenario, prompt_version)
    offer = _offer_text(scenario, discount)

    if prompt_version == "v2":
        opener = (
            "I am an AI voice agent acting on behalf of Riverline Collections. "
            "This call is recorded and logged. I am continuing from your chat: "
            f"{handoff.financial_situation}"
        )
    else:
        opener = (
            "I am an AI voice agent acting on behalf of Riverline Collections. "
            "This call is recorded and logged. I am calling about the defaulted account."
        )
    if prompt_version == "aggressive" and scenario.expected_hardship:
        agent_offer = (
            f"{offer}. You need to commit today or this will become severe for you."
        )
    elif scenario.expected_hardship:
        agent_offer = (
            "Because hardship was mentioned, I can route you to hardship review. "
            f"If you still want a standard option, {offer}."
        )
    else:
        agent_offer = offer

    messages = [
        Message(role="agent", content=opener),
        Message(role="borrower", content=_borrower_voice_reply(scenario)),
        Message(role="agent", content=agent_offer),
        Message(role="borrower", content=_borrower_commitment(scenario)),
    ]
    findings = check_compliance(messages, borrower, settlement_discount_percent=discount)
    current_summary = HandoffSummary(
        source_stage=AgentStage.RESOLUTION,
        target_stage=AgentStage.FINAL_NOTICE,
        identity_verified=handoff.identity_verified,
        borrower_position=scenario.stated_position,
        financial_situation=scenario.financial_situation,
        hardship_flags=handoff.hardship_flags,
        offers_discussed=[offer],
        objections=[scenario.behavior] if scenario.likely_resolution == "no_deal" else [],
        compliance_flags=[finding.rule_id for finding in findings if not finding.passed],
        do_not_contact=handoff.do_not_contact or scenario.asks_to_stop_contact,
        continuity_notes=(
            "Voice call completed. Final notice must reference the call offer and objections; "
            "do not ask for identity again."
        ),
    )
    merged = merge_handoffs(AgentStage.RESOLUTION, AgentStage.FINAL_NOTICE, handoff, current_summary)
    merged_text, merged_tokens = summary_to_budgeted_text(merged)
    token_counts = enforce_agent_context_budget(prompt.prompt, handoff_text)
    token_counts["handoff_input"] = handoff_tokens
    token_counts["handoff_output"] = merged_tokens
    transcript_path = _write_call_transcript(borrower.borrower_id, messages)
    return AgentRunResult(
        stage=AgentStage.RESOLUTION,
        channel=Channel.VOICE,
        messages=messages,
        outcome=_resolution_outcome(scenario, prompt_version)
        if compliance_passed(findings)
        else "compliance_failed",
        handoff_summary=merged,
        token_counts=token_counts,
        metadata={
            "prompt_version": prompt.version,
            "discount_percent": discount,
            "handoff_text": merged_text,
            "transcript_path": str(transcript_path),
            "compliance_findings": [finding.model_dump() for finding in findings],
        },
    )


def _discount_for_scenario(scenario: BorrowerScenario, prompt_version: str) -> int:
    if prompt_version == "aggressive":
        return 55
    if scenario.likely_resolution == "settlement":
        return 35
    return 20


def _offer_text(scenario: BorrowerScenario, discount: int) -> str:
    if scenario.likely_resolution == "payment_plan":
        return "a structured payment plan of four monthly payments is available with a 20% discount"
    if scenario.likely_resolution == "settlement":
        return f"a lump-sum settlement with a {discount}% discount is available for 48 hours"
    if scenario.likely_resolution == "hardship_referral":
        return "hardship-program referral is available before standard collection options continue"
    return "a final structured payment plan is available for 48 hours"


def _borrower_voice_reply(scenario: BorrowerScenario) -> str:
    replies = {
        "cooperative": "I can discuss options and want to resolve this.",
        "combative": "I do not like this process and I disagree with the amount.",
        "evasive": "I cannot say much right now and need more time.",
        "confused": "I am confused about what I owe and what happens next.",
        "distressed": "I had a medical emergency and I am under financial distress.",
    }
    return replies[scenario.behavior]


def _borrower_commitment(scenario: BorrowerScenario) -> str:
    if scenario.likely_resolution == "no_deal":
        return "I am not agreeing to a payment today."
    if scenario.likely_resolution == "hardship_referral":
        return "I want the hardship referral."
    return "I can commit to that option."


def _resolution_outcome(scenario: BorrowerScenario, prompt_version: str) -> str:
    if prompt_version == "aggressive":
        return "deal_agreed"
    if scenario.likely_resolution in {"payment_plan", "settlement"}:
        return "deal_agreed"
    if scenario.likely_resolution == "hardship_referral":
        return "hardship_referral"
    return "no_deal"


def _write_call_transcript(borrower_id: str, messages: list[Message]) -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"voice_call_{borrower_id}_{utc_timestamp().replace(':', '-')}.txt"
    path.write_text(transcript_text(messages), encoding="utf-8")
    return path
