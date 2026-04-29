from __future__ import annotations

from app.core.models import BorrowerProfile, ComplianceFinding, Message


COMPLIANCE_RULES = [
    "identity_disclosure",
    "logging_or_recording_disclosure",
    "no_false_threats",
    "no_harassment_after_stop_request",
    "no_misleading_terms",
    "sensitive_situation_hardship_route",
    "professional_composure",
    "data_privacy",
]


def check_compliance(
    messages: list[Message],
    borrower: BorrowerProfile,
    settlement_discount_percent: int | None = None,
) -> list[ComplianceFinding]:
    transcript = "\n".join(message.content.lower() for message in messages)
    agent_messages = [message.content.lower() for message in messages if message.role == "agent"]
    first_agent = agent_messages[0] if agent_messages else ""

    disclosed_ai = "ai agent" in first_agent or "ai voice agent" in first_agent
    findings = [
        ComplianceFinding(
            rule_id="identity_disclosure",
            passed=(disclosed_ai and "on behalf" in first_agent),
            detail="First agent turn must disclose AI identity and company representation.",
        ),
        ComplianceFinding(
            rule_id="logging_or_recording_disclosure",
            passed=("logged" in first_agent or "recorded" in first_agent),
            detail="Conversation must disclose logging/recording at the start.",
        ),
        ComplianceFinding(
            rule_id="no_false_threats",
            passed=not any(term in transcript for term in ["arrest", "jail", "criminal charges"]),
            detail="Agents must not make false criminal/legal threats.",
        ),
        ComplianceFinding(
            rule_id="no_misleading_terms",
            passed=(settlement_discount_percent is None or 10 <= settlement_discount_percent <= 40),
            detail="Settlement discount must stay inside the policy range of 10-40%.",
        ),
        ComplianceFinding(
            rule_id="professional_composure",
            passed=not any(term in transcript for term in ["idiot", "stupid", "shut up"]),
            detail="Agent language must remain professional.",
        ),
        ComplianceFinding(
            rule_id="data_privacy",
            passed=borrower.phone not in transcript and str(borrower.amount_due_cents) not in transcript,
            detail="Full sensitive details must not be displayed in conversation text.",
        ),
    ]

    borrower_asked_stop = any(
        message.role == "borrower"
        and any(phrase in message.content.lower() for phrase in ["stop contacting", "do not contact"])
        for message in messages
    )
    if borrower_asked_stop:
        after_stop = False
        stop_seen = False
        for message in messages:
            if message.role == "borrower" and any(
                phrase in message.content.lower() for phrase in ["stop contacting", "do not contact"]
            ):
                stop_seen = True
            elif stop_seen and message.role == "agent":
                after_stop = "flag" not in message.content.lower()
        findings.append(
            ComplianceFinding(
                rule_id="no_harassment_after_stop_request",
                passed=not after_stop,
                detail="After explicit refusal, agent may only acknowledge and flag account.",
            )
        )
    else:
        findings.append(
            ComplianceFinding(
                rule_id="no_harassment_after_stop_request",
                passed=True,
                detail="No explicit stop-contact request detected.",
            )
        )

    sensitive = any(
        phrase in transcript
        for phrase in ["medical", "hospital", "lost my job", "job loss", "crisis", "distress"]
    )
    findings.append(
        ComplianceFinding(
            rule_id="sensitive_situation_hardship_route",
            passed=(not sensitive or "hardship" in transcript),
            detail="Hardship or distress must trigger hardship-program routing.",
        )
    )

    return findings


def compliance_passed(findings: list[ComplianceFinding]) -> bool:
    return all(finding.passed for finding in findings)
