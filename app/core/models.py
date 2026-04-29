from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentStage(str, Enum):
    ASSESSMENT = "assessment"
    RESOLUTION = "resolution"
    FINAL_NOTICE = "final_notice"


class Channel(str, Enum):
    CHAT = "chat"
    VOICE = "voice"


class Message(BaseModel):
    role: Literal["system", "agent", "borrower", "judge"]
    content: str


class BorrowerProfile(BaseModel):
    borrower_id: str
    name: str
    phone: str
    partial_account_id: str
    amount_due_cents: int
    days_past_due: int
    documented_next_steps: list[str] = Field(
        default_factory=lambda: ["credit reporting", "legal referral review", "asset recovery review"]
    )


class BorrowerScenario(BaseModel):
    scenario_id: str
    behavior: Literal["cooperative", "combative", "evasive", "confused", "distressed"]
    stated_position: str
    financial_situation: str
    expected_hardship: bool = False
    asks_to_stop_contact: bool = False
    likely_resolution: Literal["payment_plan", "settlement", "hardship_referral", "no_deal"]


class HandoffSummary(BaseModel):
    source_stage: AgentStage
    target_stage: AgentStage
    identity_verified: bool = False
    borrower_position: str = ""
    financial_situation: str = ""
    hardship_flags: list[str] = Field(default_factory=list)
    offers_discussed: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    compliance_flags: list[str] = Field(default_factory=list)
    do_not_contact: bool = False
    continuity_notes: str = ""


class AgentRunResult(BaseModel):
    stage: AgentStage
    channel: Channel
    messages: list[Message]
    outcome: str
    handoff_summary: HandoffSummary | None = None
    token_counts: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceFinding(BaseModel):
    rule_id: str
    passed: bool
    detail: str


class PromptVersion(BaseModel):
    agent_stage: AgentStage
    version: str
    prompt: str
    parent_version: str | None = None
    change_note: str = ""


class StageScore(BaseModel):
    scenario_id: str
    prompt_version: str
    stage: AgentStage
    task_success: float
    continuity: float
    compliance: float
    token_efficiency: float
    borrower_experience: float
    total_score: float
    outcome: str
    violations: list[str] = Field(default_factory=list)


class EvalRun(BaseModel):
    run_id: str
    evaluator_version: str
    prompt_version: str
    scores: list[StageScore]
    mean_score: float
    compliance_pass_rate: float
    adopted: bool
    decision_reason: str
    cost_usd: float = 0.0
