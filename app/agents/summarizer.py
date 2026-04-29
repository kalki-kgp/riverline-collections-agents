from __future__ import annotations

import json

from app.core.models import AgentStage, HandoffSummary, Message
from app.core.tokens import enforce_handoff_budget


def summary_to_budgeted_text(summary: HandoffSummary) -> tuple[str, int]:
    payload = summary.model_dump(mode="json", exclude_none=True)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    tokens = enforce_handoff_budget(text)
    return text, tokens


def merge_handoffs(
    source_stage: AgentStage,
    target_stage: AgentStage,
    prior: HandoffSummary | None,
    current: HandoffSummary,
) -> HandoffSummary:
    return HandoffSummary(
        source_stage=source_stage,
        target_stage=target_stage,
        identity_verified=current.identity_verified or (prior.identity_verified if prior else False),
        borrower_position=current.borrower_position or (prior.borrower_position if prior else ""),
        financial_situation=current.financial_situation or (prior.financial_situation if prior else ""),
        hardship_flags=sorted(set((prior.hardship_flags if prior else []) + current.hardship_flags)),
        offers_discussed=(prior.offers_discussed if prior else []) + current.offers_discussed,
        objections=sorted(set((prior.objections if prior else []) + current.objections)),
        compliance_flags=sorted(set((prior.compliance_flags if prior else []) + current.compliance_flags)),
        do_not_contact=current.do_not_contact or (prior.do_not_contact if prior else False),
        continuity_notes=" ".join(
            note
            for note in [
                prior.continuity_notes if prior else "",
                current.continuity_notes,
            ]
            if note
        )[:900],
    )


def transcript_text(messages: list[Message]) -> str:
    return "\n".join(f"{message.role}: {message.content}" for message in messages)
