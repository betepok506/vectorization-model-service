import asyncio
import json
from aio_pika import connect, Message


name_queue = "text_processing"


async def send_message_async():
    cnt = 0
    while cnt < 3:
        try:
            connection = await connect(
                "amqp://admin:secret@130.100.7.137:5672/", timeout=10
            )
            async with connection:
                channel = await connection.channel()

                # Настройка подтверждения доставки
                await channel.set_qos(prefetch_count=1)

                # Объявление очереди
                # queue = await channel.declare_queue(
                #     name_queue,
                #     durable=True,
                #     arguments={'x-max-priority': 10}
                # )

                message_body = {
                    "text": "Это первый пример предложения. Вот второе предложение! И наконец третье...",
                    "message_id": "123e4567-e89b-12d3-a456-426614174000",
                    "language": "russian",
                    "metadata": {"source": "web", "author": "Иванов И.И."},
                    # 'test': "opa-opa-opa-pa"
                }

                message = Message(
                    body=json.dumps(message_body).encode(),
                    headers={"service_version": "1.0"},
                    delivery_mode=2,
                    priority=8,
                    content_type="application/json",
                    content_encoding="utf-8",
                )

                # Отправка через exchange (опционально)
                await channel.default_exchange.publish(message, routing_key=name_queue)
                print("Async message sent")

        except Exception as e:
            print(f"Error: {e}")
        cnt += 1


if __name__ == "__main__":
    asyncio.run(send_message_async())
