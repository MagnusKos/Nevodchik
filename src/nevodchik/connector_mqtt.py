import logging

import paho.mqtt.client as mqtt

from .config import ConfigApp
from .message_processor import MessageProcessor

logger = logging.getLogger(__name__)


class ConnectorMQTT:
    def __init__(self, config: ConfigApp, processor: MessageProcessor):
        self.config = config.config_mqtt
        self.processor = processor
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
        if self.processor:
            self.processor.process_mqtt_message(msg.topic, msg.payload)
        else:
            payload = ""
            try:
                payload = msg.payload.decode("utf-8", errors="ignore")
            except Exception:
                payload = msg.payload.hex()
            logger.debug(f"{msg.topic}: {msg.payload} | QoS: {msg.qos}")
        pass

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"Disconnected: {reason_code}")
        pass

    def run(self, blocking=True):
        self.setup()
        if blocking:
            logger.info("Starting MQTT client (blocking)...")
            self.client.loop_forever()
        else:
            logger.info("Starting MQTT client (non-blocking)...")
            self.client.loop_start()
        pass

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client stopped.")
