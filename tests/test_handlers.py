# type: ignore

"""
Test the handler functions. This is equivalent of e2e since the endpoints just call
these functions.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from pydantic import HttpUrl

from src.db import AsyncInMemoryDB
from src.dto import (
    BuildStage,
    Cluster,
    DeployStage,
    PipelineRequest,
    RunStage,
    StageType,
)
from src.handlers import (
    handle_create_pipeline,
    handle_delete_pipeline,
    handle_get_pipeline,
    handle_trigger_pipeline,
    handle_update_pipeline,
)


@pytest.fixture
def db() -> AsyncInMemoryDB:
    """Fixture for in-memory database instance."""
    return AsyncInMemoryDB()


@pytest.fixture
def pipeline_request() -> PipelineRequest:
    """Fixture for a sample pipeline request with multiple stages."""
    return PipelineRequest(
        name="CI Pipeline",
        git_repository=HttpUrl("https://github.com/example/repo"),
        stages=[
            RunStage(
                type=StageType.RUN, name="Run tests", command="pytest", timeout=500
            ),
            BuildStage(
                type=StageType.BUILD,
                name="Build Docker image",
                dockerfile="FROM alpine:latest",
                tag="latest",
                ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            ),
            DeployStage(
                type=StageType.DEPLOY,
                name="deploy-app-stage",
                k8s_manifest={
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {"name": "my-app"},
                    "spec": {
                        "replicas": 2,
                        "selector": {"matchLabels": {"app": "my-app"}},
                        "template": {
                            "metadata": {"labels": {"app": "my-app"}},
                            "spec": {
                                "containers": [
                                    {
                                        "name": "my-app-container",
                                        "image": "my-app-image:v1.0.0",
                                        "ports": [{"containerPort": 80}],
                                    }
                                ]
                            },
                        },
                    },
                },
                cluster=Cluster(
                    name="my-cluster",
                    server_url=HttpUrl("https://my-cluster.example.com"),
                    namespace="production",
                ),
            ),
        ],
        parallel=False,
    )


async def test_handle_create_pipeline(
    db: AsyncInMemoryDB, pipeline_request: PipelineRequest
) -> None:
    """Test creating a new pipeline."""
    response = await handle_create_pipeline(pipeline_request, db)

    assert response.message == "Pipeline created successfully."
    pipeline = await db.get(response.id)
    assert pipeline["name"] == "CI Pipeline"
    assert len(pipeline["stages"]) == 3


async def test_handle_get_pipeline(
    db: AsyncInMemoryDB, pipeline_request: PipelineRequest
):
    """Test retrieving an existing pipeline."""
    # First create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, db)

    # Then fetch it using the ID
    pipeline = await handle_get_pipeline(create_response.id, db)
    assert pipeline["name"] == "CI Pipeline"
    assert len(pipeline["stages"]) == 3

    # Check the pipeline exists in the database
    assert await db.get(create_response.id) is not None


async def test_handle_get_pipeline_not_found(db: AsyncInMemoryDB) -> None:
    """Test trying to retrieve a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_get_pipeline("non-existent-id", db)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


async def test_handle_update_pipeline(
    db: AsyncInMemoryDB, pipeline_request: PipelineRequest
) -> None:
    """Test updating an existing pipeline."""
    # First create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, db)

    # Update the pipeline
    updated_request = PipelineRequest(
        name="Updated CI Pipeline",
        git_repository=pipeline_request.git_repository,
        stages=pipeline_request.stages,
        parallel=True,
    )
    response = await handle_update_pipeline(create_response.id, updated_request, db)

    assert response.message == "Pipeline updated successfully."
    pipeline = await db.get(create_response.id)
    assert pipeline["name"] == "Updated CI Pipeline"
    assert pipeline["parallel"] is True


async def test_handle_update_pipeline_not_found(
    db: AsyncInMemoryDB, pipeline_request: PipelineRequest
):
    """Test updating a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_update_pipeline("non-existent-id", pipeline_request, db)
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


async def test_handle_delete_pipeline(
    db: AsyncInMemoryDB, pipeline_request: PipelineRequest
):
    """Test deleting an existing pipeline."""
    # First create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, db)

    # Then delete it
    response = await handle_delete_pipeline(create_response.id, db)

    assert response.message == "Pipeline deleted successfully."
    assert await db.get(create_response.id) is None


async def test_handle_delete_pipeline_not_found(db: AsyncInMemoryDB):
    """Test trying to delete a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_delete_pipeline("non-existent-id", db)
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


@patch("src.handlers._schedule_pipeline", new_callable=AsyncMock)
async def test_handle_trigger_pipeline(
    mock_schedule_pipeline: AsyncMock,
    db: AsyncInMemoryDB,
    pipeline_request: PipelineRequest,
):
    """Test triggering a pipeline with mocked stages and ensuring cleanup."""
    create_response = await handle_create_pipeline(pipeline_request, db)

    # Trigger the pipeline and ensure that tasks are executed
    response = await handle_trigger_pipeline(create_response.id, db)
    assert response.message == "Pipeline triggered successfully."

    assert mock_schedule_pipeline.await_count == 1
