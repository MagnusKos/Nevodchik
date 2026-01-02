import logging

from .config import ConfigApp
from .client_mqtt import ClientMQTT
from .message_processor import MessageProcessor

logger = logging.getLogger(__name__)

def run():
    print("Fisherman is catching fish...")
    config = ConfigApp("./tests/test.conf.local")
    print(f"{str(config)}")
    processor = MessageProcessor(config)

    client_mqtt = ClientMQTT(config, processor)

    try:
        client_mqtt.run()
    except KeyboardInterrupt:
        logger.warning("Keyboard interruption, exiting...")
        print("Keyboard interruption, exiting...")
    pass