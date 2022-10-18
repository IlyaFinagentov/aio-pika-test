import asyncio
import json
import logging
import os
import time
from typing import Dict, MutableMapping

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)


class Subscriber:
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    loop: asyncio.AbstractEventLoop
    
    def __init__(self) -> None:
        self.futures: MutableMapping[str, asyncio.Future] = {}
        self.loop = asyncio.get_running_loop()
        self.queue_name = os.environ.get('QUEUE_NAME')
    
    async def connect(self) -> "Subscriber":
        self.connection = await connect("amqp://guest:guest@rabbitmq/")
        self.channel = await self.connection.channel()
        self.exchange = self.channel.default_exchange
        self.queue = await self.channel.declare_queue(self.queue_name)

        return self
    
    def some_work(self, request: Dict) -> Dict:
        task_id = request.get("id", None)
        task_name = request.get("task_name", None)
        task_name = request.get("task_description", None)
        print(" [x] Doing some work")
        time.sleep(int(os.environ.get('SLEEP_TIME', 30)))
        return {
            "response_msg": "some response"
        }
    
    async def listener(self) -> None:
        # Start listening the queue
        async with self.queue.iterator() as qiterator:
            message: AbstractIncomingMessage
            async for message in qiterator:
                try:
                    print(" [x] Got request")
                    async with message.process(requeue=False):
                        assert message.reply_to is not None
                        msg = json.loads(message.body.decode())
                        response = json.dumps(self.some_work(msg)).encode()
                        await self.exchange.publish(
                            Message(
                                body=response,
                                correlation_id=message.correlation_id,
                            ),
                            routing_key=message.reply_to,
                        )
                        print(" [x] Request complete")
                except Exception:
                    logging.exception("Processing error for message %r", message)


async def main() -> None:
    subscriber = await Subscriber().connect()
    print(" [x] Connection success")
    await subscriber.listener()
    print(" [x] Listener success")

if __name__ == "__main__":
    asyncio.run(main())
