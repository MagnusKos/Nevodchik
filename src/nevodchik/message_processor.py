# message_processor.py
import json
import tomllib
import logging
import fnmatch
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from .config import ConfigApp
from .decoder import build_decoder_chain
from .broker import MessageBroker

logger = logging.getLogger(__name__)


@dataclass
class MessageText:
    proto: str
    sent_by: str  # hex without 0x
    heard_by: str  # hex without 0x
    ch_name: str
    rx_rssi: int
    rx_time: str
    hops: int
    text: str
    pass


@dataclass
class MessageInfo:
    proto: str
    node_id: str  # hex without 0x
    node_name: str  # readable name
    pass


class MessageProcessor:
    """
    Processes incoming MQTT messages:
    1. Filters by topic and content
    2. Decodes payload (JSON, hex, UTF-8)
    3. Formats for downstream clients
    """

    DEFAULT_TEMPLATES = {
        "text": {
            "russian": "Сообщение от {sent_by} в {ch_name}: {text}",
            "english": "Message from {sent_by} in {ch_name}: {text}",
            "compact": "[{ch_name}] {sent_by}: {text} (RSSI={rx_rssi})",
        },
    }

    def __init__(self, config: ConfigApp, broker: MessageBroker=None):
        self.config = config
        self.broker = broker
        self.templates = self._load_templates()
        self.decoder_chain = build_decoder_chain()

    def process_mqtt_message(
        self, topic: str, payload: bytes
    ) -> MessageText | MessageInfo | None:
        message_decoded = self.decoder_chain.handle(topic, payload)

        if not message_decoded:
            logger.debug("Undecoded message")
            return None

        message_final = self._format_message(message_decoded, "russian")  # just for now
        logger.info(f"{message_final}")

        self._publish_to_broker(message_final)

        return message_final

    def _should_process(self, topic: str) -> bool:
        return True  # Just for now...
        # filters = self.config.processor.filters  # ToDo
        # if not filters:
        #     return True
        # for pattern in filters.keys():
        #     if fnmatch.fnmatch(topic, pattern):
        #         return True
        # return False

    def _load_templates(
        self, config_file: str = "./config/messages.conf"
    ) -> dict[str, dict[str, str]]:
        """
        Load templates from TOML config with fallback to defaults.

        Args:
            config_file: Path to config.toml file

        Returns:
            Nested dictionary of {message_type: {template_name: template_string}}
        """
        config_path = Path(config_file)

        if config_path.is_file():
            with config_path.open("rb") as f:
                config = tomllib.load(f)
            templates = config.get("message_templates", {})

            result = self.DEFAULT_TEMPLATES.copy()
            for msg_type, msg_templates in templates.items():
                result[msg_type] = {
                    **self.DEFAULT_TEMPLATES.get(msg_type, {}),
                    **msg_templates,
                }
            return result
        else:
            logger.warning(f"Config file {self.config_path} not found, using defaults.")
            return self.DEFAULT_TEMPLATES
        pass

    def _format_message(
        self, message: MessageText, format_type: str
    ) -> str:  # ToDo: different types of msgs and defaults
        """
        Format message using loaded template.

        Args:
            message: MessageText instance
            format_type: string with format type from config (e.g. "russian")

        Returns:
            Formatted message string
        """
        
        if format_type in self.templates["text"]:
            return self.templates["text"][format_type].format(**message.__dict__)
        else:
            return self.DEFAULT_TEMPLATES["text"]["compact"].format(
                **message.__dict__
            )  # fallback of the fallback, yep
        pass

    def _publish_to_broker(self, message: str):
        if self.broker:
            self.broker.publish(message)
