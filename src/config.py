from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    username: str = "admin"
    password: str = "admin"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
