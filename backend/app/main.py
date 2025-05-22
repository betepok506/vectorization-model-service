import asyncio
import logging
import os
import signal

from rabbitmq_client import RabbitMQClient
from app.models.batch_processor import BatchProcessor
from services.vectorization_service import VectorizationService
from app.core.config import (
    RABBITMQ_URI,
    MODEL_NAME,
    LOG_LEVEL,
    LOG_JSON_FORMAT,
)

from app.core.metrics import start_metrics_server

from app.logger import setup_logger as configure_logger

configure_logger(level=LOG_LEVEL, json_format=LOG_JSON_FORMAT)

logger = logging.getLogger(__name__)


async def shutdown(signal, loop, client):
    """
    Обработчик сигналов завершения работы.

    Parameters
    ----------
    signal : signal.Signals
        Полученный сигнал (SIGINT / SIGTERM).
    loop : asyncio.AbstractEventLoop
        Текущий event loop.
    client : RabbitMQClient
        Клиент RabbitMQ для корректного завершения.
    """
    logger.info(f"Received exit signal {signal.name}")
    await client.close()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    logger.info("Cancelled all outstanding tasks")
    loop.stop()


def main():
    """
    Точка входа в микросервис векторизации.
    Запускает все компоненты и слушает очередь `vectorize_queue`.
    """
    loop = asyncio.get_event_loop()

    # Запуск сервера метрик Prometheus
    start_metrics_server(port=8000)

    client = RabbitMQClient(url=RABBITMQ_URI)
    processor = BatchProcessor(model_name=MODEL_NAME)
    service = VectorizationService(client, processor)
    # Регистрация обработчиков сигналов
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, client))
        )

    try:
        loop.run_until_complete(client.connect())
        loop.run_until_complete(service.run())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down gracefully...")
        loop.close()


if __name__ == "__main__":
    main()
