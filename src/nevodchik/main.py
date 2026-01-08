import argparse
import logging
import os

from .broker import MessageBroker
from .client_console import ClientConsole
from .client_telegram import ClientTelegram
from .config import load_config_file
from .connector_mqtt import ConnectorMQTT
from .message_processor import MessageProcessor

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


def run():
    args = parser.parse_args()
    config_file = args.config or os.environ.get("CONFIG_FILE") or default_config_file
    logger.info(f"Loading config-file: {config_file}")

    try:
        configurator = load_config_file(config_file)
    except Exception as e:
        logger.critical(f"Failed to load config: {e}")
        return

    print("Fisherman is catching fish...")

    logger.debug(f"{str(configurator)}")

    broker = MessageBroker()
    processor = MessageProcessor(configurator, broker)
    connector_mqtt = ConnectorMQTT(configurator.mqtt, processor)

    client_console = ClientConsole(configurator, broker)  # noqa: F841
    client_telegram = ClientTelegram(configurator.telegram_bots, broker)
    client_telegram.start()

    try:
        connector_mqtt.run()
    except KeyboardInterrupt:
        logger.warning("Keyboard interruption, exiting...")
        print("Keyboard interruption, exiting...")
        client_telegram.stop()
    pass
