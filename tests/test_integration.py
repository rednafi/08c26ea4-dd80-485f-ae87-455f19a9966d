"""
This makes real HTTP calls to the local API and checks the responses. This makes it a great way to test the whole system end-to-end. Also, read this file if you want to quickly understand how the
entire API suite behaves.

For this test to work, you need to have the API running locally. You can start the API by running the following command in the terminal:

```
make run-container
```

"""

from typing import ClassVar
from urllib import response

import httpx
import pytest
from fastapi import status

from tests.utils import get_basic_auth_header


@pytest.mark.integration
class TestPipelineIntegration:
    @classmethod
    def setup_class(cls) -> None:

        # Store the pipeline ID for future tests
        cls.pipeline_id = None
        cls.base_url = "http://0.0.0.0:5001"
        cls.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": get_basic_auth_header("admin", "admin"),
        }

        # Ping the server to ensure it is running
        cls.ensure_server_is_running(cls.base_url)


    @staticmethod
    def ensure_server_is_running(base_url: str) -> None:
        try:
            response = httpx.get(base_url, follow_redirects=True)
            assert response.status_code == status.HTTP_200_OK
        except Exception:
            pytest.fail(
                "Server is not running. Start the server before running integration tests. You can run `make run-container` in the terminal to start it."
            )


    async def test_create_pipeline(self) -> None:
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
            url = f"{self.base_url}/v1/pipelines/"
            response = await client.post(
                url, headers=self.headers, json=payload, follow_redirects=True
            )

            # Store the pipeline ID for the next tests
            self.__class__.pipeline_id = response.json()["id"]

            response_dict = response.json()
            assert response.status_code == status.HTTP_201_CREATED
            assert response_dict["message"] == "Pipeline created successfully."

    async def test_get_pipeline(self) -> None:
        """This test depends on the test_create_pipeline test to pass."""


        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/pipelines/{self.pipeline_id}"
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["id"] == self.pipeline_id
            assert response_dict["name"] == "CI Pipeline"

    async def test_update_pipeline(self) -> None:
        """This test depends on the test_create_pipeline test to pass."""

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
            ]
        }

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/pipelines/{self.pipeline_id}"
            response = await client.put(
                url, headers=self.headers, json=payload, follow_redirects=True
            )
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["message"] == "Pipeline updated successfully."

    async def test_trigger_pipeline(self) -> None:
        """This test depends on the test_create_pipeline test to pass."""

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/pipelines/{self.pipeline_id}/trigger"
            response = await client.post(url, headers=self.headers, follow_redirects=True)
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["message"] == "Pipeline triggered successfully."

    async def test_delete_pipeline(self) -> None:
        """This test depends on the test_create_pipeline test to pass."""

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/pipelines/{self.pipeline_id}"
            response = await client.delete(url, headers=self.headers, follow_redirects=True)
            response_dict = response.json()
            assert response.status_code == status.HTTP_200_OK
            assert response_dict["message"] == "Pipeline deleted successfully."
