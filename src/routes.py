from fastapi import APIRouter

from src.db import AsyncInMemoryDB
from src.dto import Pipeline, PipelineRequest, PipelineResponse
from src.services import (
    handle_create_pipeline,
    handle_delete_pipeline,
    handle_get_pipeline,
    handle_trigger_pipeline,
    handle_update_pipeline,
)

router = APIRouter(prefix="/v1")
db = AsyncInMemoryDB()


@router.post("/pipelines")
async def create_pipeline(pipeline: PipelineRequest) -> PipelineResponse:
    return await handle_create_pipeline(pipeline, db)


@router.get("/pipelines/{id}")
async def get_pipeline(id: str) -> Pipeline:
    return await handle_get_pipeline(id, db)


@router.put("/pipelines/{id}")
async def update_pipeline(id: str, pipeline: PipelineRequest) -> PipelineResponse:
    return await handle_update_pipeline(id, pipeline, db)


@router.delete("/pipelines/{id}")
async def delete_pipeline(id: str) -> PipelineResponse:
    return await handle_delete_pipeline(id, db)


@router.post("/pipelines/{id}/trigger")
async def trigger_pipeline(id: str) -> PipelineResponse:
    return await handle_trigger_pipeline(id, db)
