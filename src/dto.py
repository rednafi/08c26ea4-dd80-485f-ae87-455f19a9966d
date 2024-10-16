"""Data Transfer Objects for the request and responses"""

from enum import StrEnum

from pydantic import BaseModel


class StageType(StrEnum):
    RUN = "Run"
    BUILD = "Build"
    DEPLOY = "Deploy"


class RunStage(BaseModel):
    type: StageType = StageType.RUN
    command: str


class BuildStage(BaseModel):
    type: StageType = StageType.BUILD
    dockerfile: str
    ecr_repository: str


class DeployStage(BaseModel):
    type: StageType = StageType.DEPLOY
    k8s_manifest: str
    cluster: str


class Pipeline(BaseModel):
    name: str
    repository: str
    stages: list[RunStage | BuildStage | DeployStage]


PipelineRequest = Pipeline


class PipelineResponse(BaseModel):
    id: str
    message: str
