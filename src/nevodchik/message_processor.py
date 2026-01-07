# message_processor.py
import json
import logging
import fnmatch
from typing import Optional
from dataclasses import dataclass

from .config import ConfigApp
from .decoder import build_decoder_chain

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

    def __init__(self, config: ConfigApp):
        self.config = config
        self.decoder_chain = build_decoder_chain()

    def process_mqtt_message(
        self, topic: str, payload: bytes
    ) -> MessageText | MessageInfo | None:
        message_decoded = self.decoder_chain.handle(topic, payload)

        if not message_decoded:
            logger.debug("Undecoded message")
            return None

        logger.info(f"{message_decoded}")
        return message_decoded

    def _should_process(self, topic: str) -> bool:
        return True  # Just for now...
        # filters = self.config.processor.filters  # ToDo
        # if not filters:
        #     return True
        # for pattern in filters.keys():
        #     if fnmatch.fnmatch(topic, pattern):
        #         return True
        # return False
