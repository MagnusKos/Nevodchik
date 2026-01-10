import logging

from .client_base import ClientBase

logger = logging.getLogger(__name__)


class ClientConsole(ClientBase):
    """Very simple client that prints out a message to the console"""

    def __init__(self, config):
        self.config = config  # not in use

    async def send_message(self, message: str):
        """Handle incoming processed messages."""
        print(message)
        pass
