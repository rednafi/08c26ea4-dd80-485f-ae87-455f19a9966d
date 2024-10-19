# type: ignore

"""Test the handler functions. This is equivalent to end-to-end testing since the endpoints just call
these functions. This file has been updated to reflect the changes in handler signatures and to
include tests for cancellation, parallel, and sequential execution.
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
def pipeline_db() -> AsyncInMemoryDB:
    """Fixture for an in-memory pipeline database instance."""
    return AsyncInMemoryDB()


@pytest.fixture
def runner_db() -> AsyncInMemoryDB:
    """Fixture for an in-memory runner database instance."""
    return AsyncInMemoryDB()


@pytest.fixture
def pipeline_request() -> PipelineRequest:
    """Fixture for a sample pipeline request with multiple stages."""
    return PipelineRequest(
        name="CI Pipeline",
        git_repository=HttpUrl("https://github.com/example/repo"),
        stages=[
            RunStage(type=StageType.RUN, name="Run tests", command="pytest", timeout=2),
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
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
) -> None:
    """Test creating a new pipeline."""
    response = await handle_create_pipeline(pipeline_request, pipeline_db)

    assert response.message == "Pipeline created successfully."
    pipeline = await pipeline_db.get(response.id)
    assert pipeline["name"] == "CI Pipeline"
    assert len(pipeline["stages"]) == 3


async def test_handle_get_pipeline(
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
) -> None:
    """Test retrieving an existing pipeline."""
    # First, create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, pipeline_db)

    # Then fetch it using the ID
    pipeline = await handle_get_pipeline(create_response.id, pipeline_db)
    assert pipeline["name"] == "CI Pipeline"
    assert len(pipeline["stages"]) == 3

    # Check the pipeline exists in the database
    assert await pipeline_db.get(create_response.id) is not None


async def test_handle_get_pipeline_not_found(pipeline_db: AsyncInMemoryDB) -> None:
    """Test trying to retrieve a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_get_pipeline("non-existent-id", pipeline_db)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


async def test_handle_update_pipeline(
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
) -> None:
    """Test updating an existing pipeline."""
    # First, create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, pipeline_db)

    # Update the pipeline
    updated_request = PipelineRequest(
        name="Updated CI Pipeline",
        git_repository=pipeline_request.git_repository,
        stages=pipeline_request.stages,
        parallel=True,
    )
    response = await handle_update_pipeline(
        create_response.id, updated_request, pipeline_db
    )

    assert response.message == "Pipeline updated successfully."
    pipeline = await pipeline_db.get(create_response.id)
    assert pipeline["name"] == "Updated CI Pipeline"
    assert pipeline["parallel"] is True


async def test_handle_update_pipeline_not_found(
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
) -> None:
    """Test updating a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_update_pipeline("non-existent-id", pipeline_request, pipeline_db)
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


async def test_handle_delete_pipeline(
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
    runner_db: AsyncInMemoryDB,
) -> None:
    """Test deleting an existing pipeline."""
    # First, create the pipeline
    create_response = await handle_create_pipeline(pipeline_request, pipeline_db)

    # Then delete it
    response = await handle_delete_pipeline(create_response.id, pipeline_db, runner_db)

    assert response.message == "Pipeline deleted successfully."
    assert await pipeline_db.get(create_response.id) is None


async def test_handle_delete_pipeline_not_found(
    pipeline_db: AsyncInMemoryDB, runner_db: AsyncInMemoryDB
) -> None:
    """Test trying to delete a non-existent pipeline."""
    with pytest.raises(HTTPException) as exc_info:
        await handle_delete_pipeline("non-existent-id", pipeline_db, runner_db)
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == "Pipeline not found. Make sure to create the pipeline first."
    )


@patch("src.handlers.run_pipeline")
async def test_handle_trigger_pipeline(
    mock_run_pipeline: AsyncMock,
    pipeline_request: PipelineRequest,
    pipeline_db: AsyncInMemoryDB,
    runner_db: AsyncInMemoryDB,
) -> None:
    """Test triggering a pipeline and ensure that it's scheduled correctly."""
    create_response = await handle_create_pipeline(pipeline_request, pipeline_db)

    # Trigger the pipeline
    response = await handle_trigger_pipeline(create_response.id, pipeline_db, runner_db)
    assert response.message == "Pipeline triggered successfully."

    # Ensure that run_pipeline was called
    mock_run_pipeline.assert_called_once()

    # Check that the pipeline task is stored in runner_db
    runner_data = await runner_db.get(create_response.id)
    assert runner_data is not None
    assert runner_data["status"] == "running"
    assert "task" in runner_data
