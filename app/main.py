from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel
from temporalio.client import Client

from app.agents.chat import run_assessment_chat, run_final_notice_chat
from app.agents.voice import run_resolution_voice
from app.core.models import BorrowerProfile, BorrowerScenario
from app.eval.learning_loop import run_learning_loop
from app.eval.meta_eval import run_meta_evaluation
from app.eval.scenarios import demo_borrower, seeded_scenarios
from app.worker import TASK_QUEUE
from app.workflows.borrower_pipeline import BorrowerPipelineWorkflow

app = FastAPI(title="Riverline Collections Agents", version="0.1.0")


class StartWorkflowRequest(BaseModel):
    borrower: BorrowerProfile | None = None
    scenario_id: str = "S05_distressed_hardship"
    prompt_version: str = "v2"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/demo/run-direct")
async def run_direct(request: StartWorkflowRequest) -> dict:
    borrower = request.borrower or demo_borrower()
    scenario = _scenario_by_id(request.scenario_id)
    assessment = run_assessment_chat(borrower, scenario, request.prompt_version)
    resolution = run_resolution_voice(borrower, scenario, assessment.handoff_summary, request.prompt_version)
    results = [assessment, resolution]
    if resolution.outcome != "deal_agreed":
        final_notice = run_final_notice_chat(
            borrower, scenario, resolution.handoff_summary, request.prompt_version
        )
        results.append(final_notice)
    return {"results": [result.model_dump(mode="json") for result in results]}


@app.post("/workflows/start")
async def start_workflow(request: StartWorkflowRequest) -> dict[str, str]:
    target = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(target)
    borrower = request.borrower or demo_borrower()
    scenario = _scenario_by_id(request.scenario_id)
    workflow_id = f"borrower-{borrower.borrower_id}-{uuid4()}"
    handle = await client.start_workflow(
        BorrowerPipelineWorkflow.run,
        args=[borrower, scenario, request.prompt_version],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return {"workflow_id": handle.id, "temporal_address": target}


@app.post("/eval/run")
async def eval_run() -> dict[str, str]:
    return run_learning_loop()


@app.post("/eval/meta")
async def meta_eval_run() -> dict[str, str]:
    return run_meta_evaluation()


def _scenario_by_id(scenario_id: str) -> BorrowerScenario:
    for scenario in seeded_scenarios():
        if scenario.scenario_id == scenario_id:
            return scenario
    raise ValueError(f"unknown scenario_id: {scenario_id}")
