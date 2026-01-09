import asyncio
import logging
from queue import Queue
from threading import Thread
from types import List

from telegram import Bot
from telegram.error import TelegramError

from .broker import MessageBroker
from .config import ConfigTelegramBot

logger = logging.getLogger(__name__)


class ClientTelegram:
    """
    Telegram subscriber wrapping async python-telegram-bot.
    """

    def __init__(self, configs: List[ConfigTelegramBot], broker: MessageBroker):
        self.broker = broker

        self.bots = []
        for conf_tg_bot in configs:
            try:
                bot_instance = Bot(token=conf_tg_bot.token)
                self.bots.append(
                    {
                        "name": conf_tg_bot.name,
                        "bot": bot_instance,
                        "targets": conf_tg_bot.targets,
                    }
                )
                logger.info(
                    f"Initialized bot '{conf_tg_bot.name}' with {len(conf_tg_bot.targets)} targets."
                )
            except Exception as e:
                logger.error(f"Failed to init bot '{conf_tg_bot.name}': {e}")

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
        """Send message to ALL targets of ALL bots."""
        tasks = []

        for bot_entry in self.bots:
            bot = bot_entry["bot"]
            bot_name = bot_entry["name"]

            for target in bot_entry["targets"]:
                tasks.append(self._safe_send(bot, bot_name, target, message))

        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_send(self, bot, bot_name, target, message):
        """Helper to safely send to one target."""
        try:
            await bot.send_message(
                chat_id=target.chat_id, message_thread_id=target.topic_id, text=message
            )
        except TelegramError as e:
            logger.error(
                f"Bot '{bot_name}' failed to send to target '{target.description}': {e}"
            )
