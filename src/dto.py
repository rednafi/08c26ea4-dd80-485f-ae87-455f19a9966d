"""Data Transfer Objects for the request and responses."""

import re
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
)


class StageType(StrEnum):
    RUN = "Run"
    BUILD = "Build"
    DEPLOY = "Deploy"

class BaseStage(BaseModel):
    name: str = Field(..., description="Name of the stage, e.g., lint, test, build.")

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        "Name cannot be empty or start with a number."
        if not value:
            raise ValueError("Name cannot be empty.")
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number.")
        return value


class RunStage(BaseStage):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Run",
                "name": "Run tests",
                "command": "pytest",
                "timeout": 500,
            }
        }
    )
    type: Literal[StageType.RUN] = Field(
        ..., description="Type of the stage, should be 'Run'"
    )
    command: str = Field(..., description="Shell command to run in this stage.")
    timeout: int = Field(
        600, description="Timeout for the stage in seconds, default 600."
    )

    @field_validator("command")
    def validate_command(cls, value: str) -> str:
        # Pass-through validation for shell command.
        return value


class BuildStage(BaseStage):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Build",
                "name": "Build Docker image",
                "dockerfile": "FROM alpine:latest && CMD ['echo', 'Hello, World!']",
                "tag": "latest",
                "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            }
        }
    )
    type: Literal[StageType.BUILD] = Field(
        ..., description="Type of the stage, should be 'Build'"
    )
    dockerfile: str = Field(..., description="Dockerfile content.")
    tag: str = Field(..., description="Docker image tag.")
    ecr_repository: str = Field(..., description="ECR repository URL path.")

    @field_validator("dockerfile")
    def validate_dockerfile(cls, value: str) -> str:
        return value

    @field_validator("ecr_repository")
    def validate_ecr_repository(cls, value: str) -> str:
        ecr_url_pattern = (
            r"^\d{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[a-zA-Z0-9-_]+$"
        )
        if not re.match(ecr_url_pattern, value):
            raise ValueError(
                "Invalid ECR repository URL format. Please provide a valid ECR path like "
                "'123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo'.",
            )
        return value


class Cluster(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "my-cluster",
                "server_url": "https://my-cluster.example.com",
                "namespace": "default",
            }
        }
    )
    name: str = Field(..., description="Name of the Kubernetes cluster")
    server_url: HttpUrl = Field(..., description="URL of the Kubernetes cluster")
    namespace: str | None = Field(
        "default", description="Kubernetes namespace to deploy to"
    )

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        name_pattern = r"^[a-zA-Z0-9-_]+$"
        if not re.match(name_pattern, value):
            raise ValueError(
                "Invalid cluster name format. Please provide a valid cluster name."
            )
        return value

    @field_validator("namespace")
    def validate_namespace(cls, value: str) -> str:
        if not value:
            return "default"

        namespace_pattern = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
        if not re.match(namespace_pattern, value):
            raise ValueError(
                "Invalid namespace format. Please provide a valid Kubernetes namespace."
            )
        return value

    # Ensure that HttpUrl serializes as a string in Pydantic v2
    @field_serializer("server_url")
    def serialize_git_repository(self, server_url: HttpUrl) -> str:
        return str(server_url)


class DeployStage(BaseStage):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
            }
        }
    )
    type: Literal[StageType.DEPLOY] = Field(
        ..., description="Type of the stage, should be 'Deploy'"
    )
    k8s_manifest: dict[str, Any] = Field(
        ..., description="Kubernetes manifest in JSON format."
    )
    cluster: Cluster = Field(..., description="Kubernetes cluster details.")

    @field_validator("k8s_manifest")
    def validate_k8s_manifest(cls, value: dict[str, Any]) -> dict[str, Any]:
        return value


Stage = RunStage | BuildStage | DeployStage


class PipelineBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "parallel": False,
            }
        }
    )
    name: str = Field(..., description="Name of the pipeline.")
    git_repository: HttpUrl = Field(..., description="URL of the Git repository.")
    stages: list[Stage] = Field(..., description="List of stages in the pipeline.")
    parallel: bool = Field(
        default=False,
        description="Whether the stages should run in parallel or sequentially.",
    )

    # Ensure that HttpUrl serializes as a string in Pydantic v2
    @field_serializer("git_repository")
    def serialize_git_repository(self, git_repository: HttpUrl) -> str:
        return str(git_repository)

    @field_validator("stages")
    def validate_stages(cls, value: list[Stage]) -> list[Stage]:
        # Check that the names of the stages are unique

        stage_names = [stage.name for stage in value]
        if len(stage_names) != len(set(stage_names)):
            raise ValueError("Stage names must be unique.")
        return value


class Pipeline(PipelineBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                **PipelineBase.model_config["json_schema_extra"]["example"],  # type: ignore
            }
        }
    )
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the pipeline.",
        frozen=True,
    )


class PipelineRequest(PipelineBase):
    model_config = ConfigDict(
        json_schema_extra=PipelineBase.model_config["json_schema_extra"]
    )


class PipelineResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Pipeline has been successfully created.",
            }
        }
    )
    id: str
    message: str
