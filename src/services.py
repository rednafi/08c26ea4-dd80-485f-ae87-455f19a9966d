from uuid import uuid4

from fastapi import HTTPException

from src.db import AsyncDB
from src.dto import Pipeline, PipelineRequest, PipelineResponse


async def handle_create_pipeline(
    pipeline: PipelineRequest, db: AsyncDB
) -> PipelineResponse:
    pipeline_id = str(uuid4())

    await db.set(pipeline_id, pipeline.model_dump())
    return PipelineResponse(id=pipeline_id, message="Pipeline created successfully")


async def handle_get_pipeline(id: str, db: AsyncDB) -> Pipeline:
    pipeline = await db.get(id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline


async def handle_update_pipeline(
    id: str, pipeline: PipelineRequest, db: AsyncDB
) -> PipelineResponse:
    if await db.get(id) is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Validate stages
    for stage in pipeline.stages:
        if stage.type not in ["Run", "Build", "Deploy"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage type: {stage.type}. Supported types are 'Run', 'Build', 'Deploy'.",
            )

    await db.update(id, pipeline.model_dump())
    return PipelineResponse(id=id, message="Pipeline updated successfully")


async def handle_delete_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    if db.get(id) is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await db.delete(id)
    return PipelineResponse(id=id, message="Pipeline deleted successfully")


async def handle_trigger_pipeline(id: str, db: AsyncDB) -> PipelineResponse:
    if await db.get(id) is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = await db.get(id)

    for stage in pipeline["stages"]:
        if stage["type"] == "Run":
            print(f"Running command: {stage['command']}")
        elif stage["type"] == "Build":
            print(
                f"Building Docker image from {stage['dockerfile']} and pushing to {stage['ecr_repository']}"
            )
        elif stage["type"] == "Deploy":
            print(
                f"Applying Kubernetes manifest {stage['k8s_manifest']} to cluster {stage['cluster']}"
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown stage type: {stage['type']}"
            )

    return PipelineResponse(id=id, message="Pipeline triggered successfully")
