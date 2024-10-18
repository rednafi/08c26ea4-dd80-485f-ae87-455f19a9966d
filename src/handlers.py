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
from src.runner import run_pipeline

logger = logging.getLogger("pipeline.handlers")


async def handle_create_pipeline(
    pipeline_request: PipelineRequest, db: AsyncDB
) -> PipelineResponse:
    """Create a new pipeline and store it in the database."""

    pipeline = Pipeline(**pipeline_request.model_dump())

    await db.set(pipeline.id, pipeline.model_dump())
    return PipelineResponse(id=pipeline.id, message="Pipeline created successfully.")


async def handle_get_pipeline(id: str, db: AsyncDB) -> Pipeline:
    """Retrieve a pipeline from the database."""

    await _raise_when_id_not_found(id, db)
    pipeline = await db.get(id)
    return pipeline


async def handle_update_pipeline(
    id: str, pipeline_request: PipelineRequest, db: AsyncDB
) -> PipelineResponse:
    """Update an existing pipeline in the database."""

    await _raise_when_id_not_found(id, db)

    pipeline = Pipeline(**pipeline_request.model_dump())
    await db.update(id, pipeline.model_dump())
    return PipelineResponse(id=id, message="Pipeline updated successfully.")


async def handle_delete_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    """Delete a pipeline from the database."""

    await _raise_when_id_not_found(id, db)
    await db.delete(id)
    return PipelineResponse(id=id, message="Pipeline deleted successfully.")


async def handle_trigger_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    """Trigger a pipeline by running the stages sequentially in the background."""

    await _raise_when_id_not_found(id, db)
    pipeline_dict = await db.get(id)
    pipeline = Pipeline(**pipeline_dict)

    await _schedule_pipeline(pipeline, db)

    return PipelineResponse(id=id, message="Pipeline triggered successfully.")


async def _raise_when_id_not_found(id: str, db: AsyncDB) -> None:
    """Raise a 404 error if the pipeline ID is not found in the database."""

    if await db.get(id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Make sure to create the pipeline first.",
        )


async def _schedule_pipeline(pipeline: Pipeline, db: AsyncDB) -> None:
    """Schedule the pipeline stages to run in sequence."""

    logger.info("Scheduling pipeline stages...")

    asyncio.create_task(run_pipeline(pipeline, db))

    logger.info("All stages have been scheduled.")
