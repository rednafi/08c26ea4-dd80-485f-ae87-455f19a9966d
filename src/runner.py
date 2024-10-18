import asyncio
import logging
from enum import StrEnum

from src.db import AsyncDB, AsyncInMemoryDB
from src.dto import BuildStage, DeployStage, Pipeline, RunStage

# We use another instance of in-memory database to save the execution status of the pipeline stages.
runner_db = AsyncInMemoryDB()

logger = logging.getLogger("pipeline.runner")


class StageExecutionStatus(StrEnum):
    """Enumeration of the execution status of the pipeline stages."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


async def run_pipeline(pipeline: Pipeline, pipeline_db: AsyncDB) -> None:
    "Run the pipeline stages."

    # We check if the pipeline is already running. If it is, we cancel it.
    await cancel_pipeline_if_running(pipeline, runner_db)

    # Run in parallel if the pipeline is configured to do so.
    if pipeline.parallel:
        # Create a task for run_stages_in_parallel
        stages_task = asyncio.create_task(run_stages_in_parallel(pipeline, runner_db))
    else:
        # Create a task for run_stages_in_sequence
        stages_task = asyncio.create_task(run_stages_in_sequence(pipeline, runner_db))

    # We mark the pipeline as running and store the task.
    await runner_db.set(
        pipeline.id, {"status": StageExecutionStatus.RUNNING, "task": stages_task}
    )

    try:
        # Await the stages task
        await stages_task
    except asyncio.CancelledError:
        # Handle cancellation
        logger.info(f"Pipeline '{pipeline.id}' was cancelled.")
    finally:
        # We delete the pipeline from the database here, regardless of the status.
        await pipeline_db.safe_delete(pipeline.id)
        # Remove the task from runner_db
        await runner_db.safe_delete(pipeline.id)


async def cancel_pipeline_if_running(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Cancel the previously running pipeline."""

    running_pipeline = await runner_db.get(pipeline.id)
    if (
        running_pipeline
        and running_pipeline.get("status") == StageExecutionStatus.RUNNING
    ):
        logger.info(f"Pipeline '{pipeline.id}' is running. Canceling it.")
        # Cancel the task
        task = running_pipeline.get("task")
        if task:
            task.cancel()
        # Update status
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )


async def run_stages_in_sequence(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the stages in sequence."""
    logger.info(f"Running pipeline '{pipeline.id}' stages in sequence.")

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
        logger.info(f"Pipeline '{pipeline.id}' stages were cancelled.")
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )
        raise
    except Exception as e:
        logger.error(f"Failed to run stage '{stage.name}'", exc_info=e)
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.FAILED, "task": None}
        )
        raise
    else:
        # If all stages are completed, we mark the pipeline as completed
        logger.info(f"Pipeline '{pipeline.id}' stages completed successfully.")
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.COMPLETED, "task": None}
        )


async def run_stages_in_parallel(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the stages in parallel."""
    logger.info(f"Running pipeline '{pipeline.id}' stages in parallel.")

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
        logger.info(f"Pipeline '{pipeline.id}' stages were cancelled.")
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.CANCELED, "task": None}
        )
        raise
    except Exception as e:
        logger.error(f"Failed to run pipeline '{pipeline.id}'", exc_info=e)
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.FAILED, "task": None}
        )
        raise
    else:
        # If all stages are completed, we mark the pipeline as completed.
        await runner_db.update(
            pipeline.id, {"status": StageExecutionStatus.COMPLETED, "task": None}
        )


async def _execute_run_stage(stage: RunStage) -> None:
    """Execute the run stage."""
    logger.info(f"Running stage '{stage.name}' of type 'run'.")

    # Simulate the execution of the stage
    await asyncio.sleep(2)

    logger.info(f"Stage '{stage.name}' completed.")


async def _execute_build_stage(stage: BuildStage) -> None:
    """Execute the build stage."""
    logger.info(f"Running stage '{stage.name}' of type 'build'.")

    # Simulate the execution of the stage
    await asyncio.sleep(3)

    logger.info(f"Stage '{stage.name}' completed.")


async def _execute_deploy_stage(stage: DeployStage) -> None:
    """Execute the deploy stage."""
    logger.info(f"Running stage '{stage.name}' of type 'deploy'.")

    # Simulate the execution of the stage
    await asyncio.sleep(5)

    logger.info(f"Stage '{stage.name}' completed.")
