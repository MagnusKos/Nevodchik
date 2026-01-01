import pytest
import logging
import threading
import sys
import os
from pathlib import Path

from client_mqtt import ClientMQTT
from config import ConfigMQTT

logger = logging.getLogger("TestMQTT")

@pytest.mark.smoke
def test_connection_client_mqtt():
    test_conf_str = "./tests/test.conf.local"
    test_conf_path = Path(test_conf_str)

    test_conf_mqtt = ConfigMQTT(config_path_str=test_conf_str if test_conf_path.is_file() else None)
    test_client_mqtt = ClientMQTT(test_conf_mqtt)

    packet_received_event = threading.Event()
    on_message_orig = test_client_mqtt.on_message

    def on_message_interceptor(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:
            payload = msg.payload.hex()
        logger.info(f"Message:")
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
        logger.info(f"Waiting for a packet for 60 seconds.")
        received = packet_received_event.wait(timeout=60.0)
        if received:
            logger.info("Test complete.")
        else:
            pytest.fail("Timeout! No packets received in 60 seconds.")
    finally:
        test_client_mqtt.client.loop_stop()
        test_client_mqtt.client.disconnect()
    pass