"""Assemble all the API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.db import AsyncDB, AsyncInMemoryDB
from src.dto import Pipeline, PipelineRequest, PipelineResponse
from src.handlers import (
    handle_create_pipeline,
    handle_delete_pipeline,
    handle_get_pipeline,
    handle_trigger_pipeline,
    handle_update_pipeline,
)

# This allows future versioning.
router = APIRouter(prefix="/v1")

# Instantiate the in-memory databases at the application level
pipeline_db_instance = AsyncInMemoryDB()
runner_db_instance = AsyncInMemoryDB()


# Dependency that provides the same instance of the pipeline database
async def get_pipeline_db() -> AsyncDB:
    """Get the pipeline database instance."""
    return pipeline_db_instance


# Dependency that provides the same instance of the runner database
async def get_runner_db() -> AsyncDB:
    """Get the runner database instance."""
    return runner_db_instance


# Using dependency injection to provide the same instance of the database to all routes
# This allows us to easily test the route handlers by passing in a mock database instance
PipelineDB = Annotated[AsyncDB, Depends(get_pipeline_db)]
RunnerDB = Annotated[AsyncDB, Depends(get_runner_db)]


@router.post("/pipelines", status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_request: PipelineRequest, pipeline_db: PipelineDB
) -> PipelineResponse:
    """Create a pipeline."""
    return await handle_create_pipeline(pipeline_request, pipeline_db)


@router.get("/pipelines/{id}")
async def get_pipeline(id: str, pipeline_db: PipelineDB) -> Pipeline:
    """Get a pipeline by ID."""
    return await handle_get_pipeline(id, pipeline_db)


@router.put("/pipelines/{id}")
async def update_pipeline(
    id: str, pipeline_request: PipelineRequest, pipeline_db: PipelineDB
) -> PipelineResponse:
    """Update a pipeline."""
    return await handle_update_pipeline(id, pipeline_request, pipeline_db)


@router.delete("/pipelines/{id}")
async def delete_pipeline(
    id: str, pipeline_db: PipelineDB, runner_db: RunnerDB
) -> PipelineResponse:
    """Delete a pipeline."""
    return await handle_delete_pipeline(id, pipeline_db, runner_db)


@router.post("/pipelines/{id}/trigger")
async def trigger_pipeline(
    id: str, pipeline_db: PipelineDB, runner_db: RunnerDB
) -> PipelineResponse:
    """Trigger a pipeline."""
    return await handle_trigger_pipeline(id, pipeline_db, runner_db)
