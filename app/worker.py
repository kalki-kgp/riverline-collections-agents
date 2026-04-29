from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from app.workflows.activities import assessment_activity, final_notice_activity, resolution_activity
from app.workflows.borrower_pipeline import BorrowerPipelineWorkflow

TASK_QUEUE = "collections-task-queue"


async def main() -> None:
    target = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(target)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[BorrowerPipelineWorkflow],
        activities=[assessment_activity, resolution_activity, final_notice_activity],
    )
    print(f"Worker listening on {target}, task_queue={TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
