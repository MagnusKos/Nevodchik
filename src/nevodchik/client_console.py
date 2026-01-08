import logging

logger = logging.getLogger(__name__)


class ClientConsole:
    """Very simple client that listens to MessageBroker."""

    def __init__(self, config, broker):
        self.config = config  # not in use
        self.broker = broker

        if self.broker:
            self.broker.subscribe("MessageText", self.on_message)
            logger.info("Console client subscribed to messages")

    def on_message(self, message: str):
        """Handle incoming processed messages."""
        logger.info(f"[Console]\n{message}")
        print(message)
        pass
