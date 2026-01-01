import asyncio
import signal
import sys
import logging
from config import ConfigMQTT
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class ClientMQTT:
    def __init__(self, config: ConfigMQTT):
        self.config = config
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def setup(self):
        params = self.config.get_connection_params()
        self.client.username_pw_set(params['username'], params['password'])
        self.client.connect_async(
            params['hostname'], 
            params['port'], 
            keepalive=60
        )
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"Connected to {self.config.host}:{self.config.port}")
            for topic in self.config.topics:
                client.subscribe(topic, qos=2)
                logger.info(f"Subscribed to: {topic}")
        else:
            logger.warning(f"Connection failed: {reason_code}")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:
            payload = msg.payload.hex()
        logger.debug(f"{msg.topic}: {payload} | QoS: {msg.qos}")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"Disconnected: {reason_code}")
    
    def run(self):
        self.setup()
        self.client.loop_forever()

def signal_handler(sig, frame):
    logger.warning("\nShutting down...")
    sys.exit(0)
