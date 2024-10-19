# type: ignore

"""Test the runner implementation, cancelation, and error handling."""

import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import HttpUrl

from src.db import AsyncInMemoryDB
from src.dto import BuildStage, Cluster, DeployStage, Pipeline, RunStage, StageType
from src.runner import (
    StageExecutionStatus,
    cancel_pipeline_if_running,
    run_pipeline,
)


@pytest.fixture
def runner_db() -> AsyncInMemoryDB:
    """Fixture for a runner database instance."""
    return AsyncInMemoryDB()


@pytest.fixture
def pipeline() -> Pipeline:
    """Fixture for a sample pipeline."""
    return Pipeline(
        id="test-pipeline-id",
        name="Test Pipeline",
        git_repository=HttpUrl("https://github.com/example/repo"),
        stages=[
            RunStage(
                type=StageType.RUN,
                name="Run Stage",
                command="echo 'Running'",
                timeout=5,
            ),
            BuildStage(
                type=StageType.BUILD,
                name="Build Stage",
                dockerfile="FROM alpine:latest",
                tag="latest",
                ecr_repository="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            ),
            DeployStage(
                type=StageType.DEPLOY,
                name="Deploy Stage",
                k8s_manifest={
                    "apiVersion": "v1",
                    "kind": "Pod",
                    "metadata": {"name": "my-pod"},
                    "spec": {
                        "containers": [
                            {
                                "name": "my-container",
                                "image": "nginx:latest",
                            }
                        ]
                    },
                },
                cluster=Cluster(**{
                    "name": "my-cluster",
                    "server_url": "https://my-cluster.example.com",
                    "namespace": "default",
                }),
            ),
        ],
        parallel=False,
    )


async def test_run_pipeline_sequential(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test running a pipeline sequentially."""
    with ExitStack() as stack:
        mock_run_stage = stack.enter_context(
            patch("src.runner._execute_run_stage", new_callable=AsyncMock)
        )
        mock_build_stage = stack.enter_context(
            patch("src.runner._execute_build_stage", new_callable=AsyncMock)
        )
        mock_deploy_stage = stack.enter_context(
            patch("src.runner._execute_deploy_stage", new_callable=AsyncMock)
        )

        await run_pipeline(pipeline, runner_db)

        # Ensure that each stage was called once
        mock_run_stage.assert_awaited_once()
        mock_build_stage.assert_awaited_once()
        mock_deploy_stage.assert_awaited_once()

    # After completion, check that the status is COMPLETED
    status_data = await runner_db.get(pipeline.id)
    assert status_data["status"] == StageExecutionStatus.COMPLETED


async def test_run_pipeline_parallel(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test running a pipeline in parallel."""
    pipeline.parallel = True
    with ExitStack() as stack:
        mock_run_stage = stack.enter_context(
            patch("src.runner._execute_run_stage", new_callable=AsyncMock)
        )
        mock_build_stage = stack.enter_context(
            patch("src.runner._execute_build_stage", new_callable=AsyncMock)
        )
        mock_deploy_stage = stack.enter_context(
            patch("src.runner._execute_deploy_stage", new_callable=AsyncMock)
        )

        await run_pipeline(pipeline, runner_db)

        # Ensure that each stage was called once
        mock_run_stage.assert_awaited_once()
        mock_build_stage.assert_awaited_once()
        mock_deploy_stage.assert_awaited_once()

    # After completion, check that the status is COMPLETED
    status_data = await runner_db.get(pipeline.id)
    assert status_data["status"] == StageExecutionStatus.COMPLETED


async def test_cancel_pipeline_if_running(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test cancelling a running pipeline."""

    async def mock_sleep(*args, **kwargs):
        await asyncio.sleep(1)

    with ExitStack() as stack:
        stack.enter_context(
            patch("src.runner._execute_run_stage", side_effect=mock_sleep)
        )
        stack.enter_context(
            patch("src.runner._execute_build_stage", side_effect=mock_sleep)
        )
        stack.enter_context(
            patch("src.runner._execute_deploy_stage", side_effect=mock_sleep)
        )

        # Start the pipeline
        task = asyncio.create_task(run_pipeline(pipeline, runner_db))
        await runner_db.set(
            pipeline.id,
            {"status": StageExecutionStatus.RUNNING, "task": task},
        )

        # Wait a moment to let it start
        await asyncio.sleep(0.1)

        # Cancel the pipeline
        await cancel_pipeline_if_running(pipeline, runner_db)

        # Ensure the task is cancelled
        assert task.cancelled() or task.done()

        # Wait for the pipeline to update runner_db
        await asyncio.sleep(0.1)

        # Check that the status is updated to CANCELED
        status_data = await runner_db.get(pipeline.id)
        assert status_data["status"] == StageExecutionStatus.CANCELED

    # Clean up
    await runner_db.delete(pipeline.id)


async def test_run_pipeline_cancel_mid_execution(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test pipeline cancellation mid-execution."""
    pipeline.parallel = False

    async def mock_stage_execution(*args, **kwargs) -> None:
        await asyncio.sleep(1)  # Simulate a long-running stage

    with ExitStack() as stack:
        stack.enter_context(
            patch("src.runner._execute_run_stage", side_effect=mock_stage_execution)
        )
        stack.enter_context(
            patch("src.runner._execute_build_stage", new_callable=AsyncMock)
        )
        stack.enter_context(
            patch("src.runner._execute_deploy_stage", new_callable=AsyncMock)
        )

        pipeline_task = asyncio.create_task(run_pipeline(pipeline, runner_db))
        await runner_db.set(
            pipeline.id,
            {"status": StageExecutionStatus.RUNNING, "task": pipeline_task},
        )

        # Cancel the pipeline after 500ms
        await asyncio.sleep(0.5)
        pipeline_task.cancel()

        # Wait for cancellation to propagate
        try:
            await pipeline_task
        except asyncio.CancelledError:
            pass

        # Wait for the pipeline to update runner_db
        await asyncio.sleep(0.1)

        result = await runner_db.get(pipeline.id)
        assert result["status"] == StageExecutionStatus.CANCELED

    # Clean up
    await runner_db.delete(pipeline.id)


async def test_run_pipeline_error_handling(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test that the pipeline fails correctly when an exception is raised during a stage execution."""
    with patch(
        "src.runner._execute_run_stage", side_effect=Exception("Test exception")
    ):
        await run_pipeline(pipeline, runner_db)

    result = await runner_db.get(pipeline.id)
    assert result["status"] == StageExecutionStatus.FAILED


async def test_run_pipeline_completion(
    pipeline: Pipeline, runner_db: AsyncInMemoryDB
) -> None:
    """Test that a pipeline completes successfully without cancellation or errors."""
    with ExitStack() as stack:
        stack.enter_context(
            patch("src.runner._execute_run_stage", new_callable=AsyncMock)
        )
        stack.enter_context(
            patch("src.runner._execute_build_stage", new_callable=AsyncMock)
        )
        stack.enter_context(
            patch("src.runner._execute_deploy_stage", new_callable=AsyncMock)
        )

        await run_pipeline(pipeline, runner_db)

    result = await runner_db.get(pipeline.id)
    assert result["status"] == StageExecutionStatus.COMPLETED
