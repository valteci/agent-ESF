from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "development", "production"] = "local"
    log_level: str = "INFO"
    api_host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("API_HOST"))
    api_port: int = Field(default=8000, validation_alias=AliasChoices("API_PORT"))

    telegram_bot_token: SecretStr = Field(
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "TELEGRAM_API_KEY")
    )
    telegram_transport_mode: Literal["polling", "webhook"] = "polling"
    telegram_webhook_url: str | None = None
    telegram_webhook_secret: SecretStr | None = None
    telegram_allowed_user_ids: list[int] = Field(default_factory=list)
    telegram_allowed_chat_ids: list[int] = Field(default_factory=list)
    telegram_download_media: bool = True
    telegram_ack_enabled: bool = True
    telegram_ack_template: str = "recebi sua mensagem"
    telegram_polling_timeout_seconds: int = 30
    telegram_polling_sleep_seconds: float = 1.0
    telegram_clear_webhook_on_polling_start: bool = True
    telegram_base_url: str = "https://api.telegram.org"

    agent_enabled: bool = False
    agent_execution_mode: Literal["background", "inline"] = "background"
    agent_command: str = ""
    agent_timeout_seconds: int = 300
    agent_workdir: Path = Path(".")
    agent_instructions_path: Path = Path("AGENTS.md")
    agent_skills_search_roots: Annotated[list[Path], NoDecode] = Field(
        default_factory=lambda: [Path(".agents/skills"), Path(".codex/skills")]
    )

    storage_root: Path = Path("data")

    @field_validator("telegram_allowed_user_ids", "telegram_allowed_chat_ids", mode="before")
    @classmethod
    def parse_int_list(cls, value: object) -> object:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [int(item) for item in value]
        return value

    @field_validator("agent_skills_search_roots", mode="before")
    @classmethod
    def parse_path_list(cls, value: object) -> object:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [Path(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [Path(str(item)) for item in value]
        return value

    @property
    def inbox_root(self) -> Path:
        return self.storage_root / "inbox"

    @property
    def polling_state_root(self) -> Path:
        return self.storage_root / "polling_state"


@lru_cache
def get_settings() -> Settings:
    return Settings()
