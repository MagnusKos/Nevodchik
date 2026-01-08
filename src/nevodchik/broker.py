import logging
from typing import Callable, List

logger = logging.getLogger(__name__)


class MessageBroker:
    """
    Simple pub-sub broker for inter-client communication.
    Decouples MQTT-client from subscriber clients.
    """

    def __init__(self):
        self._subscribers: dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable[[str], None]):
        """
        Subscribe to messages.

        Args:
            event_type: "MessageText"
            callback: async or sync function that receives string with message
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscriber registered for: {event_type}")

    def publish(self, message: str):
        """
        Publish a message to all subscribers.

        Args:
            message: string to dispatch
        """
        # Publish to wildcard subscribers
        if "MessageText" in self._subscribers:
            for callback in self._subscribers["MessageText"]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in wildcard callback: {e}")
