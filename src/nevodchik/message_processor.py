# message_processor.py
import logging

from .config import ConfigMessageTemplates
from .decoder import build_decoder_chain
from .models import MessageInfo, MessageText

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Processes incoming MQTT messages:
    1. Filters by topic and content
    2. Decodes payload (JSON, hex, UTF-8)
    3. Formats for downstream clients
    """

    def __init__(self, config_tmplts: ConfigMessageTemplates):
        self.config_tmplts = config_tmplts
        self.decoder_chain = build_decoder_chain()

    def process_mqtt_message(self, topic: str, payload: bytes) -> str | None:
        message_decoded = self.decoder_chain.handle(topic, payload)

        if not message_decoded:
            logger.debug("Undecoded message")
            return None

        message_cooked = self._format_message(
            message_decoded, "russian"
        )  # just for now
        logger.info(f"{message_cooked}")

        return message_cooked

    def _should_process(self, topic: str) -> bool:
        return True  # Just for now...
        # filters = self.config.processor.filters  # ToDo
        # if not filters:
        #     return True
        # for pattern in filters.keys():
        #     if fnmatch.fnmatch(topic, pattern):
        #         return True
        # return False

    def _format_message(
        self, message: MessageText | MessageInfo, format_type: str
    ) -> str:  # ToDo: different types of msgs and defaults
        """
        Format message using loaded template.

        Args:
            message: MessageText instance
            format_type: string with format type from config (e.g. "russian")

        Returns:
            Formatted message string
        """

        tmplt_str = self.config_tmplts.text.get(format_type)

        if not tmplt_str:
            # Fallback logic
            tmplt_str = self.config_tmplts.text.get("compact", "Error: No template")

        return tmplt_str.format(**message.__dict__)
