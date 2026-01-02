# message_processor.py
import json
import logging
import fnmatch
from typing import Optional
from dataclasses import dataclass

from .config import ConfigApp

logger = logging.getLogger(__name__)


@dataclass
class Message:
    topic: str
    payload: str
    raw_payload: bytes
    source: str = "mqtt"


class MessageProcessor:
    """
    Processes incoming MQTT messages:
    1. Filters by topic and content
    2. Decodes payload (JSON, hex, UTF-8)
    3. Formats for downstream clients
    """

    def __init__(self, config: ConfigApp):
        self.config = config

    def process_mqtt_message(self, topic: str, payload: bytes) -> Optional[Message]:
        """
        Process an MQTT message from ClientMQTT.

        Returns:
            Message object if passed filters, None otherwise
        """
        if not self._should_process(topic):
            return None
        decoded_payload = self._decode_payload(payload)
        message = Message(
            topic=topic, payload=decoded_payload, raw_payload=payload, source="mqtt"
        )
        logger.info(f"Processed message from {topic}")
        return message

    def _should_process(self, topic: str) -> bool:
        return True  # Just for now...
        # filters = self.config.processor.filters  # ToDo
        # if not filters:
        #     return True
        # for pattern in filters.keys():
        #     if fnmatch.fnmatch(topic, pattern):
        #         return True
        # return False

    def _decode_payload(self, payload: bytes) -> str:
        try:
            return json.dumps(json.loads(payload.decode("utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        try:
            return payload.decode("utf-8", errors="ignore")
        except Exception:
            pass
        return f"<hex> {payload.hex()}"
