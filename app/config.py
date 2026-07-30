from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, sourced from environment variables / .env.

    Credentials are never hardcoded — pydantic-settings reads them from the
    process environment or a local .env file (gitignored).
    """

    moodle_base_url: str
    moodle_token: str
    database_url: str = "sqlite:///./dev.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
