"""Read configurations from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Currently, we only have the username and password for basic auth in the settings."""

    username: str = "admin"
    password: str = "admin"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
