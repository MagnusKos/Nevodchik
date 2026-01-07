import asyncio
import logging
from threading import Thread
from queue import Queue

from telegram import Bot
from telegram.error import TelegramError

from .broker import MessageBroker
from .config import ConfigApp

logger = logging.getLogger(__name__)

class ClientTelegram():
    """
    Telegram subscriber wrapping async python-telegram-bot.
    """
    
    def __init__(self, config: ConfigApp, broker: MessageBroker):
        self.config = config.config_telegram
        self.broker = broker

        self.bot = Bot(token=self.config.token)
        self.chat = self.config.chat
        self.message_queue: Queue[str] = Queue()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread: Thread | None = None
        self.running = False

        if self.broker:
            self.broker.subscribe("MessageText", self.on_message)
            logger.info("Telegram client subscribed to messages")

    def setup(self):  # Is it needed?
        pass
    
    def start(self) -> None:
        """Start the async event loop in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the async event loop and wait for thread to finish."""
        if not self.running:
            return
        
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self._stop_loop)
        if self.thread:
            self.thread.join(timeout=5)
    
    def on_message(self, message: str) -> None:
        """Queue message for sending (non-blocking, callback-safe)."""
        self.message_queue.put(message)
    
    def _run_async_loop(self) -> None:
        """Run the async event loop in background thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.create_task(self._queue_processor())
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    def _stop_loop(self) -> None:
        """Stop the running event loop."""
        self.loop.stop()
    
    async def _queue_processor(self) -> None:
        """Process queued messages asynchronously."""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.5)
                await self._send_message(message)
            except Exception:
                continue
    
    async def _send_message(self, message: str) -> None:
        """Send message to Telegram."""
        try:
            await self.bot.send_message(chat_id=self.chat, text=message)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")