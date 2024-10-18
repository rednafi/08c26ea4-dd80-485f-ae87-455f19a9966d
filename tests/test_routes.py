# type: ignore

from typing import Any
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.db import AsyncInMemoryDB
from src.dto import Pipeline, PipelineResponse
from src.main import app
from tests.utils import get_basic_auth_header

client: TestClient = TestClient(app)

# Mock database instance for all tests
mock_db: AsyncInMemoryDB = AsyncInMemoryDB()


def get_pipeline() -> dict[str, Any]:
    return {
        "name": "CI Pipeline",
        "git_repository": "https://github.com/example/repo",
        "stages": [
            {
                "type": "Run",
                "name": "Run tests",
                "command": "pytest",
                "timeout": 500,
            },
            {
                "type": "Build",
                "name": "Build Docker image",
                "dockerfile": "FROM alpine:latest && CMD ['echo', 'Hello, World!']",
                "tag": "latest",
                "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            },
            {
                "type": "Deploy",
                "name": "deploy-app-stage",
                "k8s_manifest": {
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
                "cluster": {
                    "name": "my-cluster",
                    "server_url": "https://my-cluster.example.com",
                    "namespace": "production",
                },
            },
        ],
        "parallel": True,
    }


@pytest.fixture
def mock_pipeline() -> Pipeline:
    return get_pipeline()


@patch(
    "src.routes.handle_create_pipeline",
    return_value=PipelineResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        message="Pipeline created successfully.",
    ),
)
def test_create_pipeline(
    mock_handle_create_pipeline: Any, mock_pipeline: Pipeline
) -> None:
    """Test the creation of a pipeline."""
    response = client.post(
        "/v1/pipelines",
        json=mock_pipeline,
        headers={"Authorization": get_basic_auth_header("admin", "admin")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    mock_handle_create_pipeline.assert_called_once()


@patch("src.routes.handle_get_pipeline", return_value=get_pipeline())
def test_get_pipeline(mock_handle_get_pipeline: Any) -> None:
    """Test retrieving a pipeline."""
    pipeline_id: str = "550e8400-e29b-41d4-a716-446655440000"

    response = client.get(
        f"/v1/pipelines/{pipeline_id}",
        headers={"Authorization": get_basic_auth_header("admin", "admin")},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_handle_get_pipeline.assert_called_once()


@patch(
    "src.routes.handle_update_pipeline",
    return_value=PipelineResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        message="Pipeline updated successfully.",
    ),
)
def test_update_pipeline(
    mock_handle_update_pipeline: Any, mock_pipeline: Pipeline
) -> None:
    """Test updating a pipeline."""
    pipeline_id: str = "550e8400-e29b-41d4-a716-446655440000"

    response = client.put(
        f"/v1/pipelines/{pipeline_id}",
        json=mock_pipeline,
        headers={"Authorization": get_basic_auth_header("admin", "admin")},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_handle_update_pipeline.assert_called_once()


@patch(
    "src.routes.handle_delete_pipeline",
    return_value=PipelineResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        message="Pipeline deleted successfully.",
    ),
)
def test_delete_pipeline(mock_handle_delete_pipeline: Any) -> None:
    """Test deleting a pipeline."""
    pipeline_id: str = "550e8400-e29b-41d4-a716-446655440000"

    response = client.delete(
        f"/v1/pipelines/{pipeline_id}",
        headers={"Authorization": get_basic_auth_header("admin", "admin")},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_handle_delete_pipeline.assert_called_once()


@patch(
    "src.routes.handle_trigger_pipeline",
    return_value=PipelineResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        message="Pipeline triggered successfully.",
    ),
)
def test_trigger_pipeline(mock_handle_trigger_pipeline: Any) -> None:
    """Test triggering a pipeline."""
    pipeline_id: str = "550e8400-e29b-41d4-a716-446655440000"

    response = client.post(
        f"/v1/pipelines/{pipeline_id}/trigger",
        headers={"Authorization": get_basic_auth_header("admin", "admin")},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_handle_trigger_pipeline.assert_called_once()
