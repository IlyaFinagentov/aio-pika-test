import asyncio
import json
import os
import uuid
from typing import MutableMapping

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)


class Publisher:
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    loop: asyncio.AbstractEventLoop

    def __init__(self) -> None:
        self.futures: MutableMapping[str, asyncio.Future] = {}
        self.loop = asyncio.get_running_loop()
        self.queue_name = os.environ.get('QUEUE_NAME')
        self.task = {
            "id": 1,
            "task_name": "some_task_name",
            "task_description": "some task description"
        }

    async def connect(self) -> "Publisher":
        self.connection = await connect(
            "amqp://guest:guest@rabbitmq/", loop=self.loop,
        )
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response)

        return self
    
    async def disconnect(self) -> "Publisher":
        await self.channel.close()
        return self

    def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            print(f"Bad message {message!r}")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def call(self) -> bytes:
        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()

        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(self.task).encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.queue_name,
        )

        return await future


async def main() -> None:
    publisher = await Publisher().connect()
    print(" [x] Requesting JSON")
    response = await publisher.call()
    print(f" [x] Got {response.decode()!r}")
    await publisher.disconnect()
    print(" [x] Connection closed")

if __name__ == "__main__":
    asyncio.run(main())
