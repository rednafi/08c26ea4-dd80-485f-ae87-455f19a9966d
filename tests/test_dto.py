# type: ignore
import pytest
from pydantic import ValidationError

from src.dto import (
    BuildStage,
    Cluster,
    DeployStage,
    Pipeline,
    PipelineResponse,
    RunStage,
    StageType,
)


class TestRunStage:
    def test_valid_run_stage(self) -> None:
        stage = RunStage(
            type=StageType.RUN,
            name="Run tests",
            command="pytest",
            timeout=500,
        )
        assert stage.type == StageType.RUN
        assert stage.name == "Run tests"
        assert stage.command == "pytest"
        assert stage.timeout == 500

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match=r"type\n  Field required"):
            RunStage(name="Run tests", command="pytest", timeout=500)

    def test_invalid_type(self) -> None:
        with pytest.raises(
            ValidationError, match=r"Input should be <StageType.RUN: 'Run'>"
        ):
            RunStage(
                type="InvalidType", name="Run tests", command="pytest", timeout=500
            )

    def test_missing_command(self) -> None:
        with pytest.raises(ValidationError, match=r"command\n  Field required"):
            RunStage(type=StageType.RUN, name="Run tests", timeout=500)

    def test_invalid_timeout(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be a valid integer"):
            RunStage(
                type=StageType.RUN,
                name="Run tests",
                command="pytest",
                timeout="not_a_number",
            )

    def test_invalid_name(self) -> None:
        with pytest.raises(ValidationError, match=r"Name cannot start with a number"):
            RunStage(type=StageType.RUN, name="1test", command="pytest", timeout=500)

    def test_default_timeout(self) -> None:
        stage = RunStage(type=StageType.RUN, name="Run tests", command="pytest")
        assert stage.timeout == 600


class TestBuildStage:
    def test_valid_build_stage(self) -> None:
        stage = BuildStage(
            type=StageType.BUILD,
            name="Build Docker image",
            dockerfile="FROM alpine:latest",
            tag="latest",
            ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        )
        assert stage.type == StageType.BUILD
        assert stage.name == "Build Docker image"
        assert stage.dockerfile == "FROM alpine:latest"
        assert stage.tag == "latest"
        assert (
            stage.ecr_repository
            == "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo"
        )

    def test_missing_type(self) -> None:
        with pytest.raises(ValidationError, match=r"type\n  Field required"):
            BuildStage(
                name="Build Docker image",
                dockerfile="FROM alpine",
                tag="latest",
                ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            )

    def test_invalid_type(self) -> None:
        with pytest.raises(
            ValidationError, match=r"Input should be <StageType.BUILD: 'Build'>"
        ):
            BuildStage(
                type="InvalidType",
                name="Build Docker image",
                dockerfile="FROM alpine",
                tag="latest",
                ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            )

    def test_missing_dockerfile(self) -> None:
        with pytest.raises(ValidationError, match=r"dockerfile\n  Field required"):
            BuildStage(
                type=StageType.BUILD,
                name="Build Docker image",
                tag="latest",
                ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            )

    def test_invalid_ecr_url(self) -> None:
        with pytest.raises(ValidationError, match=r"Invalid ECR repository URL format"):
            BuildStage(
                type=StageType.BUILD,
                name="Build Docker image",
                dockerfile="FROM alpine",
                tag="latest",
                ecr_repository="invalid-url",
            )


class TestDeployStage:
    def test_valid_deploy_stage(self) -> None:
        cluster = Cluster(
            name="my-cluster",
            server_url="https://my-cluster.example.com",
            namespace="production",
        )
        stage = DeployStage(
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
            cluster=cluster,
        )
        assert stage.type == StageType.DEPLOY
        assert stage.name == "deploy-app-stage"
        assert stage.cluster.name == "my-cluster"

    def test_missing_k8s_manifest(self) -> None:
        cluster = Cluster(
            name="my-cluster",
            server_url="https://my-cluster.example.com",
            namespace="production",
        )
        with pytest.raises(ValidationError, match=r"k8s_manifest\n  Field required"):
            DeployStage(type=StageType.DEPLOY, name="deploy-app-stage", cluster=cluster)

    def test_invalid_k8s_manifest_format(self) -> None:
        cluster = Cluster(
            name="my-cluster",
            server_url="https://my-cluster.example.com",
            namespace="production",
        )
        with pytest.raises(
            ValidationError, match=r"Input should be a valid dictionary"
        ):
            DeployStage(
                type=StageType.DEPLOY,
                name="deploy-app-stage",
                k8s_manifest="invalid-manifest",
                cluster=cluster,
            )


class TestCluster:
    def test_valid_cluster(self) -> None:
        cluster = Cluster(
            name="my-cluster",
            server_url="https://my-cluster.example.com",
            namespace="production",
        )
        assert cluster.name == "my-cluster"
        assert cluster.server_url.__str__() == "https://my-cluster.example.com/"
        assert cluster.namespace == "production"

    def test_default_namespace(self) -> None:
        cluster = Cluster(
            name="my-cluster", server_url="https://my-cluster.example.com"
        )
        assert cluster.namespace == "default"

    def test_invalid_cluster_name(self) -> None:
        with pytest.raises(ValidationError, match=r"Invalid cluster name format"):
            Cluster(
                name="invalid@name",
                server_url="https://my-cluster.example.com",
                namespace="production",
            )

    def test_invalid_server_url(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be a valid URL"):
            Cluster(name="my-cluster", server_url="invalid-url", namespace="production")

    def test_invalid_namespace(self) -> None:
        with pytest.raises(ValidationError, match=r"Invalid namespace format"):
            Cluster(
                name="my-cluster",
                server_url="https://my-cluster.example.com",
                namespace="InvalidNamespace!",
            )


class TestPipeline:
    def test_valid_pipeline(self) -> None:
        pipeline = Pipeline(
            name="CI Pipeline",
            git_repository="https://github.com/example/repo",
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
            ],
            parallel=True,
        )
        assert pipeline.name == "CI Pipeline"
        assert len(pipeline.stages) == 2
        assert pipeline.parallel is True

    def test_missing_git_repository(self) -> None:
        with pytest.raises(ValidationError, match=r"git_repository\n  Field required"):
            Pipeline(
                name="CI Pipeline",
                stages=[
                    RunStage(
                        type=StageType.RUN,
                        name="Run tests",
                        command="pytest",
                        timeout=500,
                    ),
                ],
            )

    def test_invalid_git_repository(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be a valid URL"):
            Pipeline(
                name="CI Pipeline",
                git_repository="invalid-url",
                stages=[],
            )


class TestPipelineResponse:
    def test_valid_pipeline_response(self) -> None:
        response = PipelineResponse(
            id="550e8400-e29b-41d4-a716-446655440000", message="Pipeline created"
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.message == "Pipeline created"
