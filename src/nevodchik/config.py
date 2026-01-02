import os
import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConfigMQTT:
    host: str
    port: int
    user: str
    passw: str
    topics: List[str]
    pass


class ConfigApp:
    def __init__(self, config_path_str: str = "./config/nevodchik.conf"):
        self.config_path = Path(config_path_str)

        # Set defaults
        self.config_mqtt = ConfigMQTT(
            host="localhost", port=1883, user="", passw="", topics=["msh/#"]
        )

        # Load actual parameters
        self._load_config()
        pass

    def _load_config(self):
        # Defaults if there are no config files or env-vars
        defaults = {
            "mqtt": {
                "host": self.config_mqtt.host,
                "port": self.config_mqtt.port,
                "user": self.config_mqtt.user,
                "passw": self.config_mqtt.passw,
                "topics": self.config_mqtt.topics,
            }
        }

        # Load from config file
        if self.config_path.is_file():
            with self.config_path.open("rb") as f:
                config_file = tomllib.load(f)
                logger.debug(f"Loaded config file: {self.config_path}")

                # Merge file config with defaults
                for section in defaults:
                    if section in config_file:
                        defaults[section].update(config_file[section])
        else:
            logger.warning(f"Config file {self.config_path} not found, using defaults.")

        # Override with environment variables
        self._apply_env_overrides(defaults)

        # Populate dataclasses
        self.config_mqtt = ConfigMQTT(**defaults["mqtt"])

        self._log_config()
        pass

    def _apply_env_overrides(self, config: Dict[str, Any]):
        env_mapping = {
            "MQTT_HOST": ("mqtt", "host"),
            "MQTT_PORT": ("mqtt", "port"),
            "MQTT_USER": ("mqtt", "user"),
            "MQTT_PASSW": ("mqtt", "passw"),
        }

        for env_key, (section, key) in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                if key == "port":
                    config[section][key] = int(value)
                else:
                    config[section][key] = value
        pass

    def _log_config(self):
        logger.info("Configuration loaded:")
        logger.info(
            f"\tMQTT: {self.config_mqtt.host}:{self.config_mqtt.port} (topics: {self.config_mqtt.topics})"
        )
        pass

    pass
