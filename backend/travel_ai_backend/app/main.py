import asyncio
import json
import logging
from typing import Dict
import contextlib
from travel_ai_backend.app.core.consumer import MessageConsumer
from travel_ai_backend.app.core.connection import ConnectionManager
from travel_ai_backend.app.core.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


class VectorizationService:
    """
    Главный класс, который объединяет логику подключения, получения сообщений и обработки батчей.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.connection_manager = ConnectionManager(config["rabbitmq_url"])
        self.processor = BatchProcessor(
            # batch_size=config.get("batch_size", 10), max_wait=config.get("max_wait", 5)
        )
        self.consumer = MessageConsumer(self.connection_manager, config, self.processor)
        self._consumer_task = None
        self._scheduler_task = None

    async def run(self) -> None:
        try:
            await self.connection_manager.connect()
            await self.consumer.setup_queues()
            self._consumer_task = asyncio.create_task(self.consumer.start_consuming())
            self._scheduler_task = asyncio.create_task(self.consumer.batch_scheduler())
            await self.connection_manager.should_stop.wait()
        except asyncio.CancelledError:
            logger.info("Service shutdown requested")
            await self.shutdown()
        finally:
            with contextlib.suppress(asyncio.CancelledError):
                if self._consumer_task:
                    self._consumer_task.cancel()
                    await self._consumer_task
                if self._scheduler_task:
                    self._scheduler_task.cancel()
                    await self._scheduler_task
            logger.debug("All tasks stopped")

    async def shutdown(self) -> None:
        logger.info("Service shutdown initiated")
        self.connection_manager.should_stop.set()

        try:
            if self._consumer_task or self._scheduler_task:
                await asyncio.wait_for(
                    asyncio.gather(
                        self._consumer_task,
                        self._scheduler_task,
                        return_exceptions=True,
                    ),
                    timeout=5.0,
                )
        except asyncio.TimeoutError:
            logger.warning("Tasks didn't finish in time, forcing shutdown")
        finally:
            await self.connection_manager.close()
            logger.info("Shutdown complete")


async def main():
    import signal

    config = {
        "rabbitmq_url": "amqp://admin:secret@130.100.7.137:5672/",
        "input_queue": "vectorize_queue",
        # "output_queue": "vector_results",
        "error_queue": "errors",
    }

    service = VectorizationService(config)

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGTERM, lambda: asyncio.create_task(service.shutdown())
    )

    try:
        await service.run()
    except KeyboardInterrupt:
        await service.shutdown()
    finally:
        # Явно закрываем все асинхронные генераторы и соединения
        await service.connection_manager.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
