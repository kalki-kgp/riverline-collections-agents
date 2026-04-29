from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from app.core.models import AgentRunResult, BorrowerProfile, BorrowerScenario

with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        assessment_activity,
        final_notice_activity,
        resolution_activity,
    )


@workflow.defn
class BorrowerPipelineWorkflow:
    @workflow.run
    async def run(
        self,
        borrower: BorrowerProfile,
        scenario: BorrowerScenario,
        prompt_version: str = "v2",
    ) -> list[AgentRunResult]:
        retry_policy = RetryPolicy(maximum_attempts=3)
        timeout = timedelta(seconds=30)

        assessment = await workflow.execute_activity(
            assessment_activity,
            args=[borrower, scenario, prompt_version],
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        resolution = await workflow.execute_activity(
            resolution_activity,
            args=[borrower, scenario, assessment.handoff_summary, prompt_version],
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        if resolution.outcome == "deal_agreed":
            return [assessment, resolution]
        final_notice = await workflow.execute_activity(
            final_notice_activity,
            args=[borrower, scenario, resolution.handoff_summary, prompt_version],
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        return [assessment, resolution, final_notice]
