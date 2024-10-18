"""API handlers."""

import asyncio
import logging

from fastapi import HTTPException, status

from src.db import AsyncDB
from src.dto import (
    BuildStage,
    DeployStage,
    Pipeline,
    PipelineRequest,
    PipelineResponse,
    RunStage,
    Stage,
)

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
    pipeline_dict = await db.get(id)
    pipeline = Pipeline(**pipeline_dict)

    # Run the pipeline stages in parallel or sequentially based on the pipeline config.
    # If sequential, run the stages one after the other in the same order as they appear in the
    # pipeline configuration. If parallel, run all the stages concurrently.
    if pipeline.parallel:
        asyncio.create_task(_run_pipeline_parallel(pipeline.stages))
    else:
        asyncio.create_task(_run_pipeline_sequential(pipeline.stages))

    # Remove the pipeline config after scheduling
    asyncio.create_task(_cleanup(id, db))

    return PipelineResponse(id=id, message="Pipeline triggered successfully")


async def _raise_when_id_not_found(id: str, db: AsyncDB) -> None:
    """Raise a 404 error if the pipeline ID is not found in the database."""

    if await db.get(id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Make sure to create the pipeline first.",
        )


async def _run_pipeline_sequential(stages: list[Stage]) -> None:
    """Run the stages in the same order as they appear in the pipeline configuration.
    No dependent stages are considered here.
    """

    logger.info("Running pipeline stages sequentially")
    for stage in stages:
        match stage:
            case RunStage():
                await _handle_run_stage(stage)
            case BuildStage():
                await _handle_build_stage(stage)
            case DeployStage():
                await _handle_deploy_stage(stage)
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown stage type: {stage['type']}",
                )


async def _run_pipeline_parallel(stages: list[Stage]) -> None:
    """Run all the stages concurrently without considering the order."""

    logger.info("Running pipeline stages in parallel")
    for stage in stages:
        match stage:
            case RunStage():
                asyncio.create_task(_handle_run_stage(stage))
            case BuildStage():
                asyncio.create_task(_handle_build_stage(stage))
            case DeployStage():
                asyncio.create_task(_handle_deploy_stage(stage))
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown stage type: {stage['type']}",
                )


async def _handle_run_stage(stage: RunStage) -> None:
    """Run the shell command in the Run stage."""
    # Sanitize shell command to prevent shell injection
    logger.info("Running command: %s", stage.command)


async def _handle_build_stage(stage: BuildStage) -> None:
    """Build a Docker image from the Dockerfile and push it to ECR."""
    logger.info(
        "Building Docker image from %s and pushing to %s",
        stage.dockerfile,
        stage.ecr_repository,
    )


async def _handle_deploy_stage(stage: DeployStage) -> None:
    """Deploy the Kubernetes manifest to the specified cluster."""
    logger.info("Deploying to cluster %s", stage.cluster.name)


async def _cleanup(id: str, db: AsyncDB) -> None:
    """Cleanup resources and remove pipeline config after a pipeline run."""
    logger.info("Cleaning up resources")

    # Remove the pipeline config from the database
    await db.delete(id)
