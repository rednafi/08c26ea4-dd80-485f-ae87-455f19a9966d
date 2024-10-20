"""Test suite for the CLI module."""

from http import HTTPStatus as status
from unittest.mock import Mock

import httpx
import pytest
from click.testing import CliRunner

from src.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for Click CLI runner."""
    return CliRunner()


def test_ping(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the ping command."""

    mock_get = Mock(
        return_value=httpx.Response(status_code=status.OK, json={"message": "Pong"})
    )
    monkeypatch.setattr(httpx, "get", mock_get)
    result = runner.invoke(cli, ["ping"])
    assert result.exit_code == 0


def test_create_pipeline_success(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating a pipeline with valid inputs."""
    mock_post: Mock = Mock(
        return_value=httpx.Response(
            status.CREATED, json={"message": "Pipeline created"}
        )
    )
    monkeypatch.setattr(httpx, "post", mock_post)

    result = runner.invoke(
        cli,
        [
            "create-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--data",
            '{"name": "test_pipeline"}',
        ],
    )

    assert result.exit_code == 0
    assert "Pipeline created" in result.output
    mock_post.assert_called_once_with(
        "http://mockserver/v1/pipelines",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"name": "test_pipeline"},
        follow_redirects=True,
    )


def test_create_pipeline_invalid_json(runner: CliRunner) -> None:
    """Test creating a pipeline with invalid JSON data."""
    result = runner.invoke(
        cli,
        [
            "create-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--data",
            "invalid_json",
        ],
    )

    assert result.exit_code == 0
    assert "Invalid JSON data" in result.output


def test_create_pipeline_server_error(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating a pipeline with server returning error."""
    mock_post = Mock(
        return_value=httpx.Response(
            status.INTERNAL_SERVER_ERROR, json={"error": "Server error"}
        )
    )
    monkeypatch.setattr(httpx, "post", mock_post)

    result = runner.invoke(
        cli,
        [
            "create-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--data",
            '{"name": "test_pipeline"}',
        ],
    )

    assert result.exit_code == 0
    assert "Server error" in result.output
    mock_post.assert_called_once_with(
        "http://mockserver/v1/pipelines",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"name": "test_pipeline"},
        follow_redirects=True,
    )


def test_get_pipeline_success(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test retrieving a pipeline with valid inputs."""
    mock_get = Mock(
        return_value=httpx.Response(
            status.OK, json={"id": "123", "name": "test_pipeline"}
        )
    )
    monkeypatch.setattr(httpx, "get", mock_get)

    result = runner.invoke(
        cli,
        [
            "get-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
        ],
    )

    assert result.exit_code == 0
    assert '"id": "123"' in result.output
    mock_get.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        follow_redirects=True,
    )


def test_get_pipeline_not_found(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test retrieving a pipeline that does not exist."""
    mock_get = Mock(
        return_value=httpx.Response(
            status.NOT_FOUND, json={"error": "Pipeline not found"}
        )
    )
    monkeypatch.setattr(httpx, "get", mock_get)

    result = runner.invoke(
        cli,
        [
            "get-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
        ],
    )

    assert result.exit_code == 0
    assert "Pipeline not found" in result.output
    mock_get.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        follow_redirects=True,
    )


def test_update_pipeline_success(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test updating a pipeline with valid inputs."""
    mock_put = Mock(
        return_value=httpx.Response(status.OK, json={"message": "Pipeline updated"})
    )
    monkeypatch.setattr(httpx, "put", mock_put)

    result = runner.invoke(
        cli,
        [
            "update-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
            "--data",
            '{"name": "updated_pipeline"}',
        ],
    )

    assert result.exit_code == 0
    assert "Pipeline updated" in result.output
    mock_put.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"name": "updated_pipeline"},
        follow_redirects=True,
    )


def test_update_pipeline_invalid_data(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test updating a pipeline with invalid data."""
    mock_put = Mock(
        return_value=httpx.Response(status.BAD_REQUEST, json={"error": "Invalid data"})
    )
    monkeypatch.setattr(httpx, "put", mock_put)

    result = runner.invoke(
        cli,
        [
            "update-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
            "--data",
            '{"invalid": "data"}',
        ],
    )

    assert result.exit_code == 0
    assert "Invalid data" in result.output
    mock_put.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"invalid": "data"},
        follow_redirects=True,
    )


def test_delete_pipeline_success(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test deleting a pipeline with valid inputs."""
    mock_delete = Mock(
        return_value=httpx.Response(status.OK, json={"message": "Pipeline deleted"})
    )
    monkeypatch.setattr(httpx, "delete", mock_delete)

    result = runner.invoke(
        cli,
        [
            "delete-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
        ],
    )

    assert result.exit_code == 0
    assert "Pipeline deleted" in result.output
    mock_delete.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        follow_redirects=True,
    )


def test_delete_pipeline_not_found(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test deleting a pipeline that does not exist."""
    mock_delete = Mock(
        return_value=httpx.Response(
            status.NOT_FOUND, json={"error": "Pipeline not found"}
        )
    )
    monkeypatch.setattr(httpx, "delete", mock_delete)

    result = runner.invoke(
        cli,
        [
            "delete-pipeline",
            "--username",
            "test_user",
            "--password",
            "test_pass",
            "--base-url",
            "http://mockserver",
            "--pipeline-id",
            "123",
        ],
    )

    assert result.exit_code == 0
    assert "Pipeline not found" in result.output
    mock_delete.assert_called_once_with(
        "http://mockserver/v1/pipelines/123",
        headers={
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzcw==",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        follow_redirects=True,
    )
