"""This module contains the logic to run the pipeline stages.

The pipeline API doesn't concern itself with the actual execution of the pipeline stages.
Instead, it delegates the execution to the runner module. This is a mocked implementation
of a task runner that simulates the execution of the pipeline stages.
"""

import asyncio
import logging
from enum import StrEnum

from src.db import AsyncDB
from src.dto import BuildStage, DeployStage, Pipeline, RunStage

logger = logging.getLogger("pipeline.runner")


class StageExecutionStatus(StrEnum):
    """Enumeration of the execution status of the pipeline stages."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


async def run_pipeline(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the pipeline stages."""
    try:
        # Run in parallel if the pipeline is configured to do so.
        if pipeline.parallel:
            await run_stages_in_parallel(pipeline, runner_db)
        else:
            await run_stages_in_sequence(pipeline, runner_db)
    except asyncio.CancelledError:
        # Handle cancellationF
        logger.info("Pipeline '%s' was cancelled.", pipeline.id)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )
        # No need to re-raise the exception since we've handled it
    except Exception as e:
        logger.error("Pipeline '%s' failed with error: '%s'", pipeline.id, e)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.FAILED, "task": None}
        )
        # Do not re-raise the exception
    else:
        # If all stages are completed, we mark the pipeline as completed
        logger.info("Pipeline '%s' completed successfully.", pipeline.id)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.COMPLETED, "task": None}
        )
    finally:
        # Remove the task reference from runner_db if it exists
        pipeline_status = await runner_db.get(pipeline.id)
        if pipeline_status:
            pipeline_status["task"] = None
            await runner_db.set(pipeline.id, pipeline_status)


async def cancel_pipeline_if_running(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Cancel the previously running pipeline."""
    running_pipeline = await runner_db.get(pipeline.id)
    if (
        running_pipeline
        and running_pipeline.get("status") == StageExecutionStatus.RUNNING
    ):
        logger.info("Pipeline '%s' is running. Canceling it.", pipeline.id)
        # Cancel the task
        task = running_pipeline.get("task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # Update status
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )


async def run_stages_in_sequence(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the stages in sequence."""
    logger.info("Running pipeline '%s' stages in sequence.", pipeline.id)

    try:
        for stage in pipeline.stages:
            match stage:
                case RunStage():
                    await _execute_run_stage(stage)
                case BuildStage():
                    await _execute_build_stage(stage)
                case DeployStage():
                    await _execute_deploy_stage(stage)
                case _:
                    raise ValueError(f"Unknown stage type: {stage.type}")
    except asyncio.CancelledError:
        # Handle cancellation
        logger.info("Pipeline '%s' stages were cancelled.", pipeline.id)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )
        raise  # Re-raise CancelledError to propagate cancellation
    except Exception as e:
        logger.error("Failed to run stage '%s'", pipeline.id, exc_info=e)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.FAILED, "task": None}
        )
        raise
    else:
        # If all stages are completed, we mark the pipeline as completed
        logger.info("Pipeline '%s' stages completed successfully.", pipeline.id)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.COMPLETED, "task": None}
        )


async def run_stages_in_parallel(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the stages in parallel."""
    logger.info("Running pipeline '%s' stages in parallel.", pipeline.id)

    try:
        async with asyncio.TaskGroup() as tg:
            for stage in pipeline.stages:
                match stage:
                    case RunStage():
                        tg.create_task(_execute_run_stage(stage))
                    case BuildStage():
                        tg.create_task(_execute_build_stage(stage))
                    case DeployStage():
                        tg.create_task(_execute_deploy_stage(stage))
                    case _:
                        raise ValueError(f"Unknown stage type: {stage.type}")
    except asyncio.CancelledError:
        # Handle cancellation
        logger.info("Pipeline '%s' stages were cancelled.", pipeline.id)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )
        raise  # Re-raise CancelledError to propagate cancellation
    except Exception as e:
        logger.error("Failed to run pipeline %s", pipeline.id, exc_info=e)
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.FAILED, "task": None}
        )
        raise
    else:
        # If all stages are completed, we mark the pipeline as completed.
        await runner_db.set(
            pipeline.id, {"status": StageExecutionStatus.COMPLETED, "task": None}
        )


async def _execute_run_stage(stage: RunStage) -> None:
    """Execute the run stage."""
    logger.info("Running stage '%s' type 'run'.", stage.name)

    # Simulate the execution of the stage
    await asyncio.sleep(2)

    logger.info("Stage '%s' completed.", stage.name)


async def _execute_build_stage(stage: BuildStage) -> None:
    """Execute the build stage."""
    logger.info("Running stage '%s' of type 'build'.", stage.name)
    logger.info("Building the application...")
    logger.info("Uploading to ecr...")

    # Simulate the execution of the stage
    await asyncio.sleep(3)

    logger.info("Stage '%s' completed.", stage.name)


async def _execute_deploy_stage(stage: DeployStage) -> None:
    """Execute the deploy stage."""
    logger.info("Running stage '%s' of type 'deploy'.", stage.name)
    logger.info("Deploying the application to k8s...")

    # Simulate the execution of the stage
    await asyncio.sleep(5)

    logger.info("Stage '%s' completed.", stage.name)
