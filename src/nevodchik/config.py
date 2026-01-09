import logging
from pathlib import Path
from typing import Dict, List, Optional

import tomli_w
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

    @classmethod
    def load(cls, main_config_file: str) -> Configurator:
        """
        The factory for creating Configurator with custom config-file path
        """

        main_config_file_path = Path(main_config_file).resolve()

        templates_config_file_path = main_config_file_path.parent / "messages.conf"

        class DynamicConfigurator(Configurator):
            model_config = Configurator.model_config.copy()
            model_config["toml_file"] = [
                main_config_file_path,
                templates_config_file_path,
            ]

        return DynamicConfigurator()

    @classmethod
    def _ensure_config_files(cls, main_config_path: Path) -> None:
        """
        Generates default config files if they are missing.
        """
        templates_config_path = main_config_path.parent / "messages.conf"

        main_config_path.parent.mkdir(parents=True, exist_ok=True)

        defaults = cls()

        if not main_config_path.exists():
            logger.info(f"Generating default main config at: {main_config_path}")
            main_data = defaults.model_dump(mode="json", exclude={"message_templates"})
            with main_config_path.open("wb") as f:
                tomli_w.dump(main_data, f)

        if not templates_config_path.exists():
            logger.info(f"Generating default templates at: {templates_config_path}")
            templates_data = {
                "message_templates": defaults.message_templates.model_dump(mode="json")
            }
            with templates_config_path.open("wb") as f:
                tomli_w.dump(templates_data, f)
