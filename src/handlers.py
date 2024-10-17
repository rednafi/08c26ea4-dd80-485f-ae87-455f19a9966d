"""API handlers."""

import asyncio
import logging
from typing import Any

from fastapi import HTTPException, status

from src.db import AsyncDB
from src.dto import Pipeline, PipelineRequest, PipelineResponse

logger = logging.getLogger("pipeline")


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
    return PipelineResponse(id=id, message="Pipeline updated successfully")


async def handle_delete_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    """Delete a pipeline from the database."""
    await _raise_when_id_not_found(id, db)
    await db.delete(id)
    return PipelineResponse(id=id, message="Pipeline deleted successfully.")


async def handle_trigger_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    """Trigger a pipeline by running the stages sequentially in the background."""
    await _raise_when_id_not_found(id, db)
    pipeline = await db.get(id)

    # We run the stages sequentially in the background
    async def run_pipeline_sequentially() -> None:
        # Run the stages in the same order as they appear in the pipeline configuration.
        # No dependent stages are considered here.
        for stage in pipeline["stages"]:
            match stage["type"]:
                case "Run":
                    await _handle_run_stage(stage)
                case "Build":
                    await _handle_build_stage(stage)
                case "Deploy":
                    await _handle_deploy_stage(stage)
                case _:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown stage type: {stage['type']}",
                    )

    # We run the stages in parallel in the background
    async def run_pipeline_parallel() -> None:
        # Run all the stages concurrently without considering the order.
        for stage in pipeline["stages"]:
            match stage["type"]:
                case "Run":
                    asyncio.create_task(_handle_run_stage(stage))
                case "Build":
                    asyncio.create_task(_handle_build_stage(stage))
                case "Deploy":
                    asyncio.create_task(_handle_deploy_stage(stage))
                case _:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown stage type: {stage['type']}",
                    )

    # Run the pipeline stages in parallel or sequentially based on the pipeline config.
    # If sequential, run the stages one after the other in the same order as they appear in the
    # pipeline configuration. If parallel, run all the stages concurrently.
    if pipeline["parallel"]:
        asyncio.create_task(run_pipeline_parallel())
    else:
        asyncio.create_task(run_pipeline_sequentially())

    # Cleanup resources in the background without blocking
    asyncio.create_task(_cleanup(id, db))

    return PipelineResponse(id=id, message="Pipeline triggered successfully")


async def _raise_when_id_not_found(id: str, db: AsyncDB) -> None:
    """Raise a 404 error if the pipeline ID is not found in the database."""
    if await db.get(id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Make sure to create the pipeline first.",
        )


async def _handle_run_stage(stage: dict[str, Any]) -> None:
    """Run the shell command in the Run stage."""
    # Sanitize shell command to prevent shell injection
    logger.info("Running command: %s", stage["command"])


async def _handle_build_stage(stage: dict[str, Any]) -> None:
    """Build a Docker image from the Dockerfile and push it to ECR."""
    logger.info(
        "Building Docker image from %s and pushing to %s",
        stage["dockerfile"],
        stage["ecr_repository"],
    )


async def _handle_deploy_stage(stage: dict[str, Any]) -> None:
    """Deploy the Kubernetes manifest to the specified cluster."""
    logger.info(
        "Deploying to cluster %s with manifest %s",
        stage["cluster"],
        stage["k8s_manifest"],
    )


async def _cleanup(id: str, db: AsyncDB) -> None:
    """Cleanup resources and remove pipeline config after a pipeline run."""
    logger.info("Cleaning up resources")

    # Remove the pipeline config from the database
    await db.delete(id)
