import logging
import threading
from pathlib import Path

import pytest

from nevodchik.broker import MessageBroker
from nevodchik.client_console import ClientConsole
from nevodchik.config import ConfigApp
from nevodchik.connector_mqtt import ConnectorMQTT
from nevodchik.message_processor import MessageProcessor, MessageText

logger = logging.getLogger("TestMQTT")


@pytest.mark.smoke
def test_connection_client_mqtt():
    test_conf_str = "./tests/test.conf.local"
    test_conf_path = Path(test_conf_str)

    test_conf = ConfigApp(
        config_path_str=test_conf_str if test_conf_path.is_file() else None
    )
    test_processor = MessageProcessor(test_conf)
    test_client_mqtt = ConnectorMQTT(test_conf, test_processor)

    packet_received_event = threading.Event()
    on_message_orig = test_client_mqtt.on_message

    def on_message_interceptor(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:
            payload = msg.payload.hex()
        logger.info("Message:")
        logger.info(f"  Topic: {msg.topic}")
        logger.info(f"  Payload: {payload}")
        packet_received_event.set()
        if on_message_orig:
            on_message_orig(client, userdata, msg)
        pass

    test_client_mqtt.client.on_message = on_message_interceptor

    try:
        test_client_mqtt.setup()
        test_client_mqtt.client.loop_start()
        logger.info("Waiting for a packet for 60 seconds.")
        received = packet_received_event.wait(timeout=60.0)
        if received:
            logger.info("Test complete.")
        else:
            pytest.fail("Timeout! No packets received in 60 seconds.")
    finally:
        test_client_mqtt.client.loop_stop()
        test_client_mqtt.client.disconnect()
    pass


@pytest.mark.smoke
def test_decoded_message():
    message = MessageText(
        proto="meshtastic",
        sent_by="aabbccdd",
        heard_by="ddccbbaa",
        ch_name="FomaKiniaev",
        rx_rssi=-1984,
        rx_time="never",
        hops=42,
        text="Lorem Ipsum",
    )

    test_conf_str = "./tests/test.conf.local"
    test_conf_path = Path(test_conf_str)

    test_conf = ConfigApp(
        config_path_str=test_conf_str if test_conf_path.is_file() else None
    )

    test_broker = MessageBroker()
    test_processor = MessageProcessor(test_conf, test_broker)
    test_client = ClientConsole(test_conf, test_broker)  # noqa: F841

    test_processor._publish_to_broker(
        test_processor._format_message(message, "russian")
    )
