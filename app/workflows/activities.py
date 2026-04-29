from __future__ import annotations

from temporalio import activity

from app.agents.chat import run_assessment_chat, run_final_notice_chat
from app.agents.voice import run_resolution_voice
from app.core.models import AgentRunResult, BorrowerProfile, BorrowerScenario, HandoffSummary
from app.core.store import RUNS_DIR, append_jsonl


@activity.defn
async def assessment_activity(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    prompt_version: str = "v2",
) -> AgentRunResult:
    result = run_assessment_chat(borrower, scenario, prompt_version)
    append_jsonl(RUNS_DIR / "workflow_events.jsonl", result.model_dump(mode="json"))
    return result


@activity.defn
async def resolution_activity(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    handoff: HandoffSummary,
    prompt_version: str = "v2",
) -> AgentRunResult:
    result = run_resolution_voice(borrower, scenario, handoff, prompt_version)
    append_jsonl(RUNS_DIR / "workflow_events.jsonl", result.model_dump(mode="json"))
    return result


@activity.defn
async def final_notice_activity(
    borrower: BorrowerProfile,
    scenario: BorrowerScenario,
    handoff: HandoffSummary,
    prompt_version: str = "v2",
) -> AgentRunResult:
    result = run_final_notice_chat(borrower, scenario, handoff, prompt_version)
    append_jsonl(RUNS_DIR / "workflow_events.jsonl", result.model_dump(mode="json"))
    return result
