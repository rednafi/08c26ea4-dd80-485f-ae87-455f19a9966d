"""API handlers."""

import asyncio
import logging

from fastapi import HTTPException, status

from src.db import AsyncDB
from src.dto import (
    Pipeline,
    PipelineRequest,
    PipelineResponse,
)
from src.runner import (
    StageExecutionStatus,
    cancel_pipeline_if_running,
    run_pipeline,
)

logger = logging.getLogger("pipeline.handlers")


async def handle_create_pipeline(
    pipeline_request: PipelineRequest, pipeline_db: AsyncDB
) -> PipelineResponse:
    """Create a new pipeline and store it in the database."""
    pipeline = Pipeline(**pipeline_request.model_dump())

    await pipeline_db.set(pipeline.id, pipeline.model_dump())
    return PipelineResponse(id=pipeline.id, message="Pipeline created successfully.")


async def handle_get_pipeline(pipeline_id: str, pipeline_db: AsyncDB) -> Pipeline:
    """Retrieve a pipeline from the database."""
    await _raise_when_id_not_found(pipeline_id, pipeline_db)
    pipeline = await pipeline_db.get(pipeline_id)
    return pipeline


async def handle_update_pipeline(
    pipeline_id: str, pipeline_request: PipelineRequest, pipeline_db: AsyncDB
) -> PipelineResponse:
    """Update an existing pipeline in the database."""
    await _raise_when_id_not_found(pipeline_id, pipeline_db)

    pipeline = Pipeline(**pipeline_request.model_dump())
    await pipeline_db.set(pipeline_id, pipeline.model_dump())
    return PipelineResponse(id=pipeline_id, message="Pipeline updated successfully.")


async def handle_delete_pipeline(
    pipeline_id: str, pipeline_db: AsyncDB, runner_db: AsyncDB
) -> PipelineResponse:
    """Delete a pipeline from the database."""
    await _raise_when_id_not_found(pipeline_id, pipeline_db)
    # Cancel any running pipeline before deletion
    pipeline_dict = await pipeline_db.get(pipeline_id)
    pipeline = Pipeline(**pipeline_dict)
    await cancel_pipeline_if_running(pipeline, runner_db)
    await pipeline_db.delete(pipeline_id)
    return PipelineResponse(id=pipeline_id, message="Pipeline deleted successfully.")


async def handle_trigger_pipeline(
    pipeline_id: str, pipeline_db: AsyncDB, runner_db: AsyncDB
) -> PipelineResponse:
    """Trigger a pipeline by running the stages sequentially in the background."""
    await _raise_when_id_not_found(pipeline_id, pipeline_db)
    pipeline_dict = await pipeline_db.get(pipeline_id)
    pipeline = Pipeline(**pipeline_dict)

    await _schedule_pipeline(pipeline, runner_db)

    return PipelineResponse(id=pipeline_id, message="Pipeline triggered successfully.")


async def _raise_when_id_not_found(pipeline_id: str, pipeline_db: AsyncDB) -> None:
    """Raise a 404 error if the pipeline ID is not found in the database."""
    if await pipeline_db.get(pipeline_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Make sure to create the pipeline first.",
        )


async def _schedule_pipeline(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Schedule the pipeline stages to run."""
    logger.info("Scheduling pipeline stages...")

    # Cancel if already running
    await cancel_pipeline_if_running(pipeline, runner_db)

    # Schedule run_pipeline and store the task in runner_db
    pipeline_task = asyncio.create_task(run_pipeline(pipeline, runner_db))

    # Store the task in runner_db (this could be remote call, mocking this for now)
    await runner_db.set(
        pipeline.id, {"status": StageExecutionStatus.RUNNING, "task": pipeline_task}
    )

    logger.info("Pipeline has been scheduled.")
