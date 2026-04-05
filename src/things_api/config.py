"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

CONFIG_DIR = Path.home() / ".config" / "things-api"
CONFIG_FILE = CONFIG_DIR / "config"


def _env_files() -> tuple[str, ...]:
    """Return env files in priority order (later entries override earlier ones)."""
    files: list[str] = []
    cwd_env = Path(".env")
    if cwd_env.is_file():
        files.append(str(cwd_env))
    if CONFIG_FILE.is_file():
        files.append(str(CONFIG_FILE))
    return tuple(files)


class Settings(BaseSettings):
    """Things API configuration.

    All values can be set via environment variables, a CWD .env file,
    or ~/.config/things-api/config.
    """

    things_api_host: str = "0.0.0.0"
    things_api_port: int = 5225
    things_api_token: SecretStr
    things_auth_token: SecretStr | None = None
    things_db_path: Path | None = None
    things_verify_timeout: float = 0.5

    model_config = {"env_file": _env_files(), "env_file_encoding": "utf-8"}

    @property
    def write_enabled(self) -> bool:
        """Whether write operations are available."""
        return self.things_auth_token is not None and bool(
            self.things_auth_token.get_secret_value()
        )
