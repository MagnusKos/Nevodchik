import asyncio
import logging
from typing import List

from telegram import Bot
from telegram.error import TelegramError

from .config import ConfigTelegramBot

logger = logging.getLogger(__name__)


class ClientTelegram:
    """
    Telegram-bot helper on top of the python-telegram-bot.
    """

    def __init__(self, configs: List[ConfigTelegramBot]):
        self.bots = []
        for conf_tg_bot in configs:  # Need to add checks for this list
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

        self.running = False
        pass

    async def send_message(self, message: str) -> None:
        """Send message to ALL targets of ALL bots."""
        tasks = []

        for bot_entry in self.bots:
            bot = bot_entry["bot"]
            bot_name = bot_entry["name"]

            for target in bot_entry["targets"]:
                tasks.append(self._safe_send(bot, bot_name, target, message))

        if tasks:
            await asyncio.gather(*tasks)
        pass

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
        pass
