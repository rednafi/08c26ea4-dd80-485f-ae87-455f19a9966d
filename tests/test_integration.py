"""This makes real HTTP calls to local API endpoints and checks the responses, making it a great way
to test the whole system end-to-end. Read this file if you want a quick understanding of how the
entire API suite behaves.

For this test to work, you need to have the API server running locally. Start the server by running:

```
make run-container
```

Note: Tests must be run in order. Pytest-order is used to ensure this. Running them one by one
isn't recommended, as the tests depend on each other.
"""

import asyncio

import httpx
import pytest
from fastapi import status

from src.utils import get_basic_auth_header


# Redefine the event_loop fixture with session scope
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Define fixtures for shared resources
@pytest.fixture(scope="session")
def base_url():
    return "http://0.0.0.0:5001"


@pytest.fixture(scope="session")
def headers():
    return {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": get_basic_auth_header("admin", "admin"),
    }


@pytest.fixture(scope="session", autouse=True)
async def ensure_server_is_running(base_url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, follow_redirects=True)
            assert response.status_code == status.HTTP_200_OK
    except Exception:
        pytest.fail(
            "Server is not running. Start the server before running integration tests. You can run `make run-container` in the terminal to start it."
        )


@pytest.fixture(scope="session")
async def pipeline_id(base_url, headers):
    # Create a new pipeline and yield its ID
    payload = {
        "git_repository": "https://github.com/example/repo",
        "name": "CI Pipeline",
        "parallel": False,
        "stages": [
            {
                "command": "pytest",
                "name": "Run tests",
                "timeout": 500,
                "type": "Run",
            },
            {
                "dockerfile": "FROM alpine:latest && CMD ['echo', 'Hello, World!']",
                "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
                "name": "Build Docker image",
                "tag": "latest",
                "type": "Build",
            },
            {
                "cluster": {
                    "name": "my-cluster",
                    "namespace": "production",
                    "server_url": "https://my-cluster.example.com",
                },
                "k8s_manifest": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": "my-app",
                    },
                    "spec": {
                        "replicas": 2,
                        "selector": {
                            "matchLabels": {
                                "app": "my-app",
                            },
                        },
                        "template": {
                            "metadata": {
                                "labels": {
                                    "app": "my-app",
                                },
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "image": "my-app-image:v1.0.0",
                                        "name": "my-app-container",
                                        "ports": [
                                            {
                                                "containerPort": 80,
                                            },
                                        ],
                                    },
                                ],
                            },
                        },
                    },
                },
                "name": "deploy-app-stage",
                "type": "Deploy",
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        url = f"{base_url}/v1/pipelines/"
        response = await client.post(
            url, headers=headers, json=payload, follow_redirects=True
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_dict = response.json()
        assert response_dict["message"] == "Pipeline created successfully."
        pipeline_id = response_dict["id"]

    yield pipeline_id

    # Teardown: Delete the pipeline after tests
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/v1/pipelines/{pipeline_id}"
        response = await client.delete(url, headers=headers, follow_redirects=True)
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        assert response_dict["message"] == "Pipeline deleted successfully."


class TestPipelineIntegration:
    async def test_get_pipeline(self, base_url, headers, pipeline_id):
        """Test to get the created pipeline by ID."""
        async with httpx.AsyncClient() as client:
            url = f"{base_url}/v1/pipelines/{pipeline_id}/"
            response = await client.get(url, headers=headers, follow_redirects=True)
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["id"] == pipeline_id
            assert response_dict["name"] == "CI Pipeline"

    async def test_update_pipeline(self, base_url, headers, pipeline_id):
        """Test to update the created pipeline."""
        payload = {
            "git_repository": "https://github.com/example/repo",
            "name": "CI Pipeline Updated",
            "parallel": True,
            "stages": [
                {
                    "command": "pytest",
                    "name": "Run tests",
                    "timeout": 500,
                    "type": "Run",
                },
            ],
        }

        async with httpx.AsyncClient() as client:
            url = f"{base_url}/v1/pipelines/{pipeline_id}"
            response = await client.put(
                url, headers=headers, json=payload, follow_redirects=True
            )
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["message"] == "Pipeline updated successfully."

    async def test_trigger_pipeline(self, base_url, headers, pipeline_id):
        """Test to trigger the created pipeline."""
        async with httpx.AsyncClient() as client:
            url = f"{base_url}/v1/pipelines/{pipeline_id}/trigger"
            response = await client.post(url, headers=headers, follow_redirects=True)
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["message"] == "Pipeline triggered successfully."
