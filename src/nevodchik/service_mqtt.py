import logging
from asyncio import Queue, sleep

from aiomqtt import Client, MqttError

from .config import ConfigMQTT

logger = logging.getLogger(__name__)


class ServiceMQTT:
    def __init__(self, config: ConfigMQTT, queue: Queue):
        self.config = config
        self.queue = queue

    async def run(self):
        reconnect_interval = 5
        while True:
            try:
                async with Client(
                    hostname=self.config.host,
                    port=self.config.port,
                    username=self.config.user,
                    password=self.config.passw,
                ) as client:
                    for topic in self.config.topics:
                        await client.subscribe(topic)
                        logger.info(f"Subscribed to: {topic}")

                    async for message in client.messages:
                        await self.queue.put(message)

            except MqttError as e:
                logger.error(
                    f"MQTT Error: {e}. Reconnecting in {reconnect_interval}s..."
                )
                await sleep(reconnect_interval)

    pass
