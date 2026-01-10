import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ClientBase(ABC):
    """Abstract base class for every client"""

    @abstractmethod
    async def send_message():
        """Send a message asynchronously."""
        pass
