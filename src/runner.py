"""The pipeline service doesn't concern itself with the execution of the pipeline stages. It only
stores the configuration and schedules the stage runs. We pretend that the execution of the stages are handled by these runners that runs remotely on some runner machine."""

import asyncio
import logging
from enum import StrEnum
from contextlib import suppress
from src.db import AsyncDB, AsyncInMemoryDB
from src.dto import BuildStage, DeployStage, Pipeline, RunStage

# We use another instance of in-memory database to save the execution status of the pipeline stages.
runner_db = AsyncInMemoryDB()

logger = logging.getLogger("pipeline.runner")


class StageExecutionStatus(StrEnum):
    """Enumeration of the execution status of the pipeline stages."""

    # We currently don't handle pending status.

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


async def run_pipeline(pipeline: Pipeline, pipeline_db: AsyncDB) -> None:
    "Run the pipeline stages."

    # We check if the pipeline is already running. If it is, we cancel it.
    await cancel_pipeline_if_running(pipeline, runner_db)

    # We mark the pipeline as running.
    await runner_db.set(pipeline.id, StageExecutionStatus.RUNNING)

    # Run in parallel if the pipeline is configured to do so.
    if pipeline.parallel:
        await run_stages_in_parallel(pipeline, runner_db)
    else:
        await run_stages_in_sequence(pipeline, runner_db)

    # We delete the pipeline from the database here, regardless of the status.
    with suppress(Exception):
        await pipeline_db.delete(pipeline.id)


async def cancel_pipeline_if_running(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Cancel the previously running pipeline."""

    if await runner_db.get(pipeline.id) == StageExecutionStatus.RUNNING:
        logger.info(f"Pipeline '{pipeline.id}' is running. Canceling it.")
        await runner_db.update(pipeline.id, StageExecutionStatus.CANCELED)


async def run_stages_in_sequence(pipeline: Pipeline, runner_db: AsyncDB) -> None:
    """Run the stages in sequence."""
    logger.info(f"Running pipeline '{pipeline.id}' stages in sequence.")

    for stage in pipeline.stages:
        try:
            match stage:
                case RunStage():
                    await _execute_run_stage(stage)
                case BuildStage():
                    await _execute_build_stage(stage)
                case DeployStage():
                    await _execute_deploy_stage(stage)
                case _:
                    raise ValueError(f"Unknown stage type: {stage.type}")
        except Exception as e:
            logger.error(f"Failed to run stage '{stage.name}': {e}", exc_info=e)
            return await runner_db.update(pipeline.id, StageExecutionStatus.FAILED)

    # If all stages are completed, we mark the pipeline as completed.
    await runner_db.update(pipeline.id, StageExecutionStatus.COMPLETED)


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
    except Exception as e:
        logger.error(f"Failed to run pipeline '{pipeline.id}': {e}")
        await runner_db.update(pipeline.id, StageExecutionStatus.FAILED)

    # If all stages are completed, we mark the pipeline as completed.
    await runner_db.update(pipeline.id, StageExecutionStatus.COMPLETED)


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
