import os
import logging
import argparse

from .config import ConfigApp
from .connector_mqtt import ConnectorMQTT
from .message_processor import MessageProcessor
from .broker import MessageBroker
from .client_console import ClientConsole

default_config_file = "./config/nevodchik.conf"

LOG_LEVEL = os.getenv("LOG_LEVEL", "CRITICAL")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    datefmt="%H:%M:%S",
    format="%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(prog="Nevodchik")
parser.add_argument("-c", "--config", type=str)


def run():
    args = parser.parse_args()
    config = ConfigApp(
        args.config or os.environ.get("CONFIG_FILE") or default_config_file
    )

    print("Fisherman is catching fish...")

    logger.info(f"{str(config)}")

    broker = MessageBroker()
    processor = MessageProcessor(config, broker)
    connector_mqtt = ConnectorMQTT(config, processor)

    client_console = ClientConsole(config, broker)

    try:
        connector_mqtt.run()
    except KeyboardInterrupt:
        logger.warning("Keyboard interruption, exiting...")
        print("Keyboard interruption, exiting...")
    pass
