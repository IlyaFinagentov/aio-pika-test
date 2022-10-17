import asyncio
import json
import logging
import time
from typing import Dict

from aio_pika import Message, connect
from aio_pika.abc import AbstractIncomingMessage


def some_work(request: Dict) -> Dict:
        task_id = request.get("id", None)
        task_name = request.get("task_name", None)
        task_name = request.get("task_description", None)
        time.sleep(3)
        return {
            "response_msg": "some response"
        }
        


async def main() -> None:
    # Perform connection
    connection = await connect("amqp://guest:guest@rabbitmq/")

    # Creating a channel
    channel = await connection.channel()
    exchange = channel.default_exchange

    # Declaring queue
    queue = await channel.declare_queue("rpc_queue")

    print(" [x] Awaiting RPC requests")

    # Start listening the queue
    async with queue.iterator() as qiterator:
        message: AbstractIncomingMessage
        async for message in qiterator:
            try:
                async with message.process(requeue=False):
                    assert message.reply_to is not None
                    print(1)
                    msg = json.loads(message.body.decode())
                    print(2)
                    response = json.dumps(some_work(msg)).encode()
                    print(3)
                    await exchange.publish(
                        Message(
                            body=response,
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )
                    print("Request complete")
            except Exception:
                logging.exception("Processing error for message %r", message)

if __name__ == "__main__":
    asyncio.run(main())
