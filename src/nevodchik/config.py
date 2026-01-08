import logging
from typing import List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

logger = logging.getLogger(__name__)


class ConfigMQTT(BaseModel):
    host: str = "localhost"
    port: int = 1883
    user: str | None = None
    passw: str | None = None
    topics: List[str] = ["msh/#"]


class ConfigTelegramBot(BaseModel):
    name: str = "MainBot"
    token: str
    targets: List[TargetTelegramBot] = []


class TargetTelegramBot(BaseModel):
    """Represents chats with topics for Telegram bot"""

    descr: str = "MainChat"
    chat_id: int
    topic_id: Optional[int] = None


class ConfigApp(BaseSettings):
    mqtt: ConfigMQTT = ConfigMQTT()
    telegram_bots: List[ConfigTelegramBot] = []

    model_config = SettingsConfigDict(
        toml_file="config/nevodchik.conf",
        env_prefix="NVD_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Read TOML files
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
