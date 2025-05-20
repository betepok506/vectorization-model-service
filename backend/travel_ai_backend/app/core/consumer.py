import json
import asyncio
import json
from typing import Dict, Tuple, List
from aio_pika import (
    IncomingMessage,
    Message,
)
from travel_ai_backend.app.core.logging_middleware import LoggingMiddleware
from travel_ai_backend.app.core.batch_processor import BatchProcessor
from travel_ai_backend.app.core.connection import ConnectionManager
from travel_ai_backend.app.core.validation import MessageValidator
import logging

logger = logging.getLogger(__name__)


class MessageConsumer:
    """
    Класс для получения сообщений из очереди, формирования батчей и запуска их обработки.
    Отделяет логику получения и формирования батчей от логики соединения.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        config: Dict,
        processor: BatchProcessor,
    ):
        self.connection_manager = connection_manager
        self.config = config
        self.processor = processor
        self.pending_messages: List[Tuple[Dict, IncomingMessage]] = []
        self._batch_lock = asyncio.Lock()
        self.middleware = LoggingMiddleware(service_name="MessageConsumer")

    async def setup_queues(self) -> None:
        await self.connection_manager.ensure_connection()
        # Объявляем входную очередь
        await self.connection_manager.channel.declare_queue(
            self.config["input_queue"],
            durable=True,
            arguments={"x-max-priority": 10, "x-queue-type": "classic"},
        )
        # Объявляем выходную очередь (для результатов) и очередь ошибок
        # await self.connection_manager.channel.declare_queue(
        #     self.config["output_queue"],
        #     durable=True,
        #     arguments={"x-queue-type": "classic"},
        # )
        await self.connection_manager.channel.declare_queue(
            self.config["error_queue"],
            durable=True,
            arguments={"x-queue-type": "classic"},
        )

    async def handle_message(self, message: IncomingMessage) -> None:

        @self.middleware.wrap_consumer
        async def _inner_handler(message: IncomingMessage):
            async with message.process():
                try:
                    payload = MessageValidator.validate(message)
                    async with self._batch_lock:
                        self.pending_messages.append((payload, message))
                        
                    if len(self.pending_messages) >= self.processor.batch_size:
                        await self.process_batch()
                except Exception as e:
                    # logger.error(f"Message processing error: {e}")
                    await self.send_error(e, message)

        await _inner_handler(message)

    async def process_batch(self) -> None:
        async with self._batch_lock:
            if not self.pending_messages:
                return
            batch = self.pending_messages[: self.processor.batch_size]
            self.pending_messages = self.pending_messages[self.processor.batch_size :]
        try:
            texts = [msg.text for msg, _ in batch]
            vectors = await self.processor.process_text(texts)
            for (original_msg, message), vector in zip(batch, vectors):
                result = {
                    "message_id": original_msg.message_id,
                    "vector": vector,
                    "metadata": original_msg.metadata,
                    "callback_queue": original_msg.callback_queue
                }
                await self.send_result(result, message.correlation_id)
        except Exception as e:
            for _, message in batch:
                await self.send_error(e, message)

    async def send_result(self, result: Dict, correlation_id: str) -> None:
        message = Message(
            body=json.dumps(result).encode(),
            correlation_id=correlation_id,
            delivery_mode=2,  # устойчивое сообщение
        )
        await self.connection_manager.channel.default_exchange.publish(
            message,
            routing_key=result["callback_queue"],
        )

    async def send_error(
        self, error: Exception, original_message: IncomingMessage
    ) -> None:
        error_msg = {
            "error": str(error),
            "original_message": original_message.body.decode(),
            "correlation_id": original_message.correlation_id,
        }
        message = Message(
            body=json.dumps(error_msg).encode(),
            delivery_mode=2,
        )
        await self.connection_manager.channel.default_exchange.publish(
            message,
            routing_key=self.config["error_queue"],
        )

    async def batch_scheduler(self) -> None:
        """
        Периодически запускает обработку оставшихся сообщений в батче,
        если они накопились, но пока не достигли размера батча.
        """
        while not self.connection_manager.should_stop.is_set():
            await asyncio.sleep(self.processor.max_wait)
            if self.pending_messages:
                await self.process_batch()

    async def start_consuming(self) -> None:
        try:
            channel = await self.connection_manager.get_channel()
            queue = await channel.get_queue(self.config["input_queue"])
            await queue.consume(self.handle_message)
            logger.info("Started consuming messages")

            while not self.connection_manager.should_stop.is_set():
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Consuming failed: {e}")
            await self.connection_manager.close()
            raise
