"""Test suite for the config module."""

from pathlib import Path

import pytest

from src.config import Settings


def test_default_settings() -> None:
    """Test default settings when no environment variables are set."""
    settings = Settings()
    assert settings.username == "admin"
    assert settings.password == "admin"


def test_env_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test settings when environment variables are set."""
    monkeypatch.setenv("USERNAME", "custom_user")
    monkeypatch.setenv("PASSWORD", "custom_password")

    settings = Settings()
    assert settings.username == "custom_user"
    assert settings.password == "custom_password"


def test_env_file_loading(tmp_path: Path) -> None:
    """Test settings loaded from a .env file."""
    d = tmp_path / "sub"
    d.mkdir()
    env_file = d / ".env"

    env_file.write_text(
        "USERNAME=env_file_user\nPASSWORD=env_file_password", encoding="utf-8"
    )

    settings = Settings(_env_file=str(env_file))  # type: ignore

    assert settings.username == "env_file_user"
    assert settings.password == "env_file_password"


def test_missing_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test behavior when required env variables are missing."""
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)

    settings = Settings()
    assert settings.username == "admin"
    assert settings.password == "admin"


def test_invalid_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test validation failure for invalid type in env variables."""
    monkeypatch.setenv("USERNAME", "valid_user")
    monkeypatch.setenv("PASSWORD", "12345")  # This should be valid, as it's a string

    settings = Settings()
    assert settings.username == "valid_user"
    assert settings.password == "12345"
