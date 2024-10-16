import logging
from io import StringIO
from typing import Any

from _pytest.logging import LogCaptureFixture  # for caplog fixture typing

from src.logger import configure_logger


def test_configure_logger(caplog: LogCaptureFixture) -> None:
    # Clear any handlers attached to the logger from previous tests
    logger = logging.getLogger("pipeline")
    logger.handlers = []

    # Call the function that configures the logger
    configure_logger()

    # Test if logger is configured properly
    with caplog.at_level(logging.INFO, logger="pipeline"):
        logger.info("Test log message")

    # Check if the log was captured and formatted correctly
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[0].message == "Test log message"

    # Check if the time format in the log is correct
    log_time: Any = caplog.records[0].asctime
    assert isinstance(log_time, str)
    assert len(log_time) == 19  # "YYYY-MM-DD HH:MM:SS" is 19 characters long


def test_log_output_format() -> None:
    # Set up a StringIO stream to capture log output
    stream: StringIO = StringIO()
    handler: logging.StreamHandler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)

    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("pipeline")
    logger.handlers = []  # Remove any pre-existing handlers
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Log a message and capture the output
    logger.info("Pipeline execution started")

    # Flush the handler and get the output
    handler.flush()
    log_output: str = stream.getvalue()

    # Check the log output format
    assert "pipeline - INFO - Pipeline execution started" in log_output
    assert log_output.startswith("20")  # The log should start with a year like "2024"
