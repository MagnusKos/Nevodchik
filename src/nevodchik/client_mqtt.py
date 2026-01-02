import asyncio
import signal
import sys
import logging
from config import ConfigApp
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class ClientMQTT:
    def __init__(self, config: ConfigApp):
        self.config = config.config_mqtt
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        pass

    def setup(self):
        self.client.username_pw_set(self.config.user or None, self.config.passw or None)
        self.client.connect_async(self.config.host, self.config.port, keepalive=60)
        pass

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"Connected to {self.config.host}:{self.config.port}")
            for topic in self.config.topics:
                client.subscribe(topic, qos=2)
                logger.info(f"Subscribed to: {topic}")
        else:
            logger.warning(f"Connection failed: {reason_code}")
        pass

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:
            payload = msg.payload.hex()
        logger.debug(f"{msg.topic}: {payload} | QoS: {msg.qos}")
        pass

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"Disconnected: {reason_code}")
        pass

    def run(self):
        self.setup()
        self.client.loop_forever()
        pass
