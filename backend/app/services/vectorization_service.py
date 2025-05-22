import asyncio
import logging
from typing import Dict

from app.models.batch_processor import BatchProcessor
from app.rabbitmq_client import RabbitMQClient
from app.schemas.vectorize_request import VectorizeRequestSchema
from app.core.config import (
    INPUT_QUEUE
)
logger = logging.getLogger(__name__)


class VectorizationService:
    """Сервис для векторизации текста через RabbitMQ."""

    def __init__(self, rabbitmq: RabbitMQClient, batch_processor: BatchProcessor):
        """
        Инициализирует сервис векторизации.

        Parameters
        ----------
        rabbitmq : RabbitMQClient
            Подключённый клиент RabbitMQ.
        batch_processor : BatchProcessor
            Объект, выполняющий пакетную векторизацию.
        """
        self.rabbitmq = rabbitmq
        self.processor = batch_processor
        self.pending_tasks = {}

    async def handle_vectorize_request(self, message: Dict):
        """
        Обрабатывает запрос на векторизацию текста.

        Parameters
        ----------
        message : dict
            JSON-сообщение, соответствующее схеме `VectorizeRequestSchema`.
        """
        try:
            schema = VectorizeRequestSchema(**message)
            message_id = message.get("message_id", "unknown")
            extra = {"message_id": message_id}
            logger.debug(f"Received request {schema.message_id}", extra=extra)
            await self.processor.add_to_batch(
                {
                    "message_id": schema.message_id,
                    "text": schema.text,
                    "callback": lambda res: self.send_result(
                        schema.callback_queue, res
                    ),
                }
            )
        except Exception as e:
            logger.error(f"Invalid message format: {e}")

    async def send_result(self, queue_name: str, result: dict):
        """
        Отправляет результат в указанную очередь.

        Parameters
        ----------
        queue_name : str
            Имя целевой очереди.
        result : dict
            Результат векторизации.
        """
        try:
            await self.rabbitmq.publish(queue_name, result)
            logger.debug(f"Sent result for {result['message_id']}")
        except Exception as e:
            logger.error(f"Failed to send result: {e}")

    async def run(self):
        """
        Запускает микросервис — регистрирует обработчики и начинает прослушивание очередей.
        """
        self.rabbitmq.register_handler(INPUT_QUEUE, self.handle_vectorize_request)
        await self.rabbitmq.start_consumers()
        logger.info("Service started")
