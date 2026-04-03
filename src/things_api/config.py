"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Things API configuration.

    All values can be set via environment variables or a .env file.
    """

    things_api_host: str = "0.0.0.0"
    things_api_port: int = 5225
    things_api_token: str
    things_auth_token: str | None = None
    things_db_path: Path | None = None
    things_verify_timeout: float = 0.5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def write_enabled(self) -> bool:
        """Whether write operations are available."""
        return self.things_auth_token is not None
