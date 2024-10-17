"""Assemble all the API routes."""

from fastapi import APIRouter, Depends

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

# Instantiate the in-memory database at the application level
db_instance = AsyncInMemoryDB()


# Dependency that provides the same instance of the database
async def get_db() -> AsyncDB:
    return db_instance


@router.post("/pipelines")
async def create_pipeline(
    pipeline: PipelineRequest, db: AsyncDB = Depends(get_db)
) -> PipelineResponse:
    return await handle_create_pipeline(pipeline, db)


@router.get("/pipelines/{id}")
async def get_pipeline(id: str, db: AsyncDB = Depends(get_db)) -> Pipeline:
    return await handle_get_pipeline(id, db)


@router.put("/pipelines/{id}")
async def update_pipeline(
    id: str, pipeline: PipelineRequest, db: AsyncDB = Depends(get_db)
) -> PipelineResponse:
    return await handle_update_pipeline(id, pipeline, db)


@router.delete("/pipelines/{id}")
async def delete_pipeline(id: str, db: AsyncDB = Depends(get_db)) -> PipelineResponse:
    return await handle_delete_pipeline(id, db)


@router.post("/pipelines/{id}/trigger")
async def trigger_pipeline(id: str, db: AsyncDB = Depends(get_db)) -> PipelineResponse:
    return await handle_trigger_pipeline(id, db)
