import argparse
import asyncio
import logging
import os
from typing import List

from .client_console import ClientConsole
from .client_telegram import ClientTelegram
from .config import Configurator
from .message_processor import MessageProcessor
from .service_mqtt import ServiceMQTT

LOG_LEVEL = os.getenv("LOG_LEVEL", "CRITICAL")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    datefmt="%H:%M:%S",
    format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(prog="Nevodchik")
parser.add_argument("-c", "--config", type=str)

default_config_file = "./config/nevodchik.conf"


class Application:
    def __init__(self, clients: List | None, configurator: Configurator | None):
        self.is_running = False

        if configurator:
            self.configurator = configurator
        else:
            self.configurator = Configurator()

        self.queue_service = asyncio.Queue()
        self.service_mqtt = ServiceMQTT(self.configurator.mqtt, self.queue_service)
        self.processor = MessageProcessor(self.configurator.message_templates)

        if clients:
            self.clients = clients
        else:
            self.clients = [
                ClientConsole(configurator),  # noqa: F841
                ClientTelegram(configurator.telegram_bots),
            ]
        pass

    async def _worker(self):
        logger.info("Application worker started.")
        while self.is_running:
            message_raw = await self.queue_service.get()

            try:
                message_cooked = self.processor.process_mqtt_message(
                    message_raw.topic.value, message_raw.payload
                )
                if message_cooked:
                    for client in (
                        self.clients
                    ):  # fire-and-forget 'cause some clients could be sluggish
                        asyncio.create_task(client.send_message(message_cooked))

            except Exception as e:
                logger.exception(f"Error processing message: {e}")
            finally:
                self.queue_service.task_done()
        pass

    async def run(self):
        self.is_running = True
        worker_task = asyncio.create_task(self._worker())

        await self.service_mqtt.run()

        self.is_running = False
        worker_task.cancel()


def run():
    """Nevodchik's entry point."""
    args = parser.parse_args()
    config_file = args.config or os.environ.get("CONFIG_FILE") or default_config_file
    logger.info(f"Loading config-file: {config_file}")

    try:
        configurator = Configurator.load(config_file)
    except Exception as e:
        logger.critical(f"Failed to load config: {e}")
        return

    print("Fisherman is catching fish...")
    app = Application(configurator=configurator)

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.warning("Keyboard interruption, exiting...")
        print("Keyboard interruption, exiting...")
    pass
