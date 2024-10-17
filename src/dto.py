"""Data Transfer Objects for the request and responses."""

from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class StageType(StrEnum):
    RUN = "Run"
    BUILD = "Build"
    DEPLOY = "Deploy"


class RunStage(BaseModel):
    type: Literal[StageType.RUN] = Field(
        ..., description="Type of the stage, should be 'Run'"
    )
    name: str = Field(..., description="Name of the stage, e.g., lint, test.")
    command: str = Field(..., description="Shell command to run in this stage.")


class BuildStage(BaseModel):
    type: Literal[StageType.BUILD] = Field(
        ..., description="Type of the stage, should be 'Build'"
    )
    dockerfile: str = Field(..., description="Path to the Dockerfile.")
    ecr_repository_url: str = Field(..., description="ECR repository URL.")

    @field_validator("dockerfile")
    def validate_dockerfile(cls, value: str) -> str:
        return value

    @field_validator("ecr_repository_url")
    def validate_ecr_url(cls, value: str) -> str:
        # # Regular expression for validating ECR URL
        # ecr_url_pattern = (
        #     r"^\d{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[a-zA-Z0-9-_]+$"
        # )
        # if not re.match(ecr_url_pattern, value):
        #     raise ValueError("Invalid ECR repository URL format.")
        return value


class DeployStage(BaseModel):
    type: Literal[StageType.DEPLOY] = Field(
        ..., description="Type of the stage, should be 'Deploy'"
    )
    k8s_manifest: str = Field(..., description="Path to the Kubernetes manifest file.")
    cluster: str = Field(..., description="Name of the Kubernetes cluster.")


class PipelineBase(BaseModel):
    name: str = Field(..., description="Name of the pipeline.")
    git_repository: str = Field(..., description="URL of the Git repository.")
    stages: list[RunStage | BuildStage | DeployStage] = Field(
        ..., description="List of stages in the pipeline."
    )


class Pipeline(PipelineBase):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the pipeline.",
        frozen=True,
    )


class PipelineRequest(PipelineBase):
    pass


class PipelineResponse(BaseModel):
    id: str
    message: str
