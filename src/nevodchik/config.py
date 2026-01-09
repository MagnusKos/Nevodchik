import logging
from pathlib import Path
from typing import Dict, List, Optional

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


class ConfigMessageTemplates(BaseModel):
    text: Dict[str, str] = {
        "russian": "Сообщение от {sent_by} в {ch_name}: {text}",
        "english": "Message from {sent_by} in {ch_name}: {text}",
        "compact": "[{ch_name}] {sent_by}: {text} (RSSI={rx_rssi})",
    }


class TargetTelegramBot(BaseModel):
    """Represents chats with topics for Telegram bot"""

    descr: str = "MainChat"
    chat_id: int
    topic_id: Optional[int] = None


class Configurator(BaseSettings):
    mqtt: ConfigMQTT = ConfigMQTT()
    telegram_bots: List[ConfigTelegramBot] = []
    message_templates: ConfigMessageTemplates = ConfigMessageTemplates()

    model_config = SettingsConfigDict(
        toml_file=["config/nevodchik.conf", "config/messages.conf"],
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


def load_config_file(main_config_file: str) -> Configurator:
    """The factory for creating ConfigApp with custom config-file path"""

    main_config_file_path = Path(main_config_file).resolve()

    templates_config_file_path = main_config_file_path.parent / "messages.conf"

    class DynamicConfigurator(Configurator):
        model_config = Configurator.model_config.copy()
        model_config["toml_file"] = [main_config_file_path, templates_config_file_path]

    return DynamicConfigurator()
