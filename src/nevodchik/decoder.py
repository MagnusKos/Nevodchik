import logging
from abc import ABC, abstractmethod

from .models import MessageInfo, MessageText

logger = logging.getLogger(__name__)


class Decoder(ABC):
    """Abstract base decoder."""

    def __init__(self, next_decoder: Decoder | None = None):
        """Initialize decoder with optional next decoder in chain."""
        self.next_decoder = next_decoder

    @abstractmethod
    def can_decode(self, topic: str, payload: bytes) -> bool:
        """Check if this decoder can handle the message."""
        pass

    @abstractmethod
    def decode(self, topic: str, payload: bytes) -> MessageText | MessageInfo | None:
        """Decode the message. Return None if decoding fails."""
        pass

    def handle(self, topic: str, payload: bytes) -> MessageText | MessageInfo | None:
        """Process message through chain of responsibility."""
        if self.can_decode(topic, payload):
            try:
                result = self.decode(topic, payload)
                if result is not None:
                    logger.debug(f"Decoded by {self.__class__.__name__}")
                    return result
            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__}: {e}")

        if self.next_decoder:
            return self.next_decoder.handle(topic, payload)

        logger.warning(f"No decoder found for {topic}")
        return None

    def set_next(self, decoder: Decoder) -> Decoder:
        """Set the next decoder in the chain."""
        self.next_decoder = decoder
        return decoder


def build_decoder_chain() -> Decoder:
    """
    Build the decoder chain.
    Order matters: more specific decoders first, fallback last.
    """
    # Lazy import to avoid circular imports
    from .decoder_meshtastic import DecoderMeshtastic

    meshtastic = DecoderMeshtastic()

    return meshtastic
