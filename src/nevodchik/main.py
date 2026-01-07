import os
import logging
import argparse

from .config import ConfigApp
from .client_mqtt import ClientMQTT
from .message_processor import MessageProcessor

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

    processor = MessageProcessor(config)
    client_mqtt = ClientMQTT(config, processor)

    try:
        client_mqtt.run()
    except KeyboardInterrupt:
        logger.warning("Keyboard interruption, exiting...")
        print("Keyboard interruption, exiting...")
    pass
