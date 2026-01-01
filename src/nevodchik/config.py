import os
import tomllib
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class ConfigMQTT:
    def __init__(self, config_path_str: str = "./config/nevodchik.conf"):
        self.host = ""
        self.port = 0
        self.user = ""
        self.passw = ""
        self.topics = []

        self.config_path_str = config_path_str
        self._load_config()

    def log_params(self):
        logger.info("Config in use:")
        logger.info(f"\tHost: {self.host}")
        logger.info(f"\tPort: {self.port}")
        logger.info(f"\tUser: {self.user }")
        logger.info(f"\tPassw: {self.passw }")
        logger.info(f"\tTopics: {self.topics}")
        pass

    def _load_config(self):
        config_default = {
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "user": "",
                "passw": "",
                "topics": ["msh/#"],
            }
        }

        config_path = Path(self.config_path_str)
        if config_path.is_file():
            with config_path.open(mode="rb") as f:
                config_file = tomllib.load(f)
                logger.debug(f"Loaded config file: {config_file}.")
                config_default["mqtt"].update(config_file.get("mqtt", {}))
        else:
            logger.warning(
                f"Config file {self.config_path_str} not found, using defaults."
            )

        config_mqtt = config_default["mqtt"]
        env_mapping = {
            "MQTT_HOST": config_mqtt["host"],
            "MQTT_PORT": config_mqtt["port"],
            "MQTT_USER": config_mqtt["user"],
            "MQTT_PASSW": config_mqtt["passw"],
        }

        for env_key, default_value in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                if env_key == "MQTT_PORT":
                    config_mqtt["port"] = int(env_value)
                else:
                    config_mqtt[env_key.lower().replace("mqtt_", "")] = env_value

        self.host = config_mqtt["host"]
        self.port = config_mqtt["port"]
        self.user = config_mqtt["user"]
        self.passw = config_mqtt["passw"]
        self.topics = config_mqtt["topics"]
        self.log_params()
        pass

    def get_connection_params(self):
        return {
            "hostname": self.host,
            "port": self.port,
            "username": self.user or None,
            "password": self.passw or None,
        }

