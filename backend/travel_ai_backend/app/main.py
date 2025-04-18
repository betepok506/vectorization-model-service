import asyncio
import json
import logging
from typing import Dict
import contextlib
from travel_ai_backend.app.core.consumer import MessageConsumer
from travel_ai_backend.app.core.connection import ConnectionManager
from travel_ai_backend.app.core.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


# class ConnectionManager:
#     """Класс для управления соединением и переподключением к RabbitMQ."""

#     def __init__(
#         self,
#         rabbitmq_url: str,
#         max_reconnect_attempts: int = 10,
#         reconnect_delay: int = 5,
#     ):
#         self.rabbitmq_url = rabbitmq_url
#         self._max_reconnect_attempts = max_reconnect_attempts
#         self._base_delay = reconnect_delay

#         self.connection: RobustConnection = None
#         self.channel: Channel = None
#         # Событие, которое сигнализирует об успешно установленном подключении
#         self._is_connected = asyncio.Event()
#         self._should_stop = asyncio.Event()

#         self._connection_lock = asyncio.Lock()

#     @property
#     def is_connected(self) -> bool:
#         return (
#             self._is_connected.is_set()
#             and self.connection
#             and not self.connection.is_closed
#         )

#     async def connect(self) -> None:
#         async with self._connection_lock:
#             attempts = 0
#             while not self._should_stop.is_set():
#                 try:
#                     self.connection = await connect(
#                         self.rabbitmq_url,
#                         timeout=10,
#                         client_properties={"connection_name": "vectorization_service"},
#                     )
#                     self.channel = await self.connection.channel()
#                     # Пример установки QoS – значение можно сделать параметризуемым
#                     await self.channel.set_qos(prefetch_count=100)
#                     self._is_connected.set()
#                     logger.info("Successfully connected to RabbitMQ")
#                     return
#                 except (AMQPConnectionError, ConnectionError, OSError) as e:
#                     attempts += 1
#                     logger.error(f"Connection attempt {attempts} failed: {str(e)}")
#                     if attempts >= self._max_reconnect_attempts:
#                         logger.error("Max reconnect attempts reached. Exiting...")
#                         self._should_stop.set()
#                         raise e
#                     delay = self._base_delay * attempts
#                     logger.info(f"Next connection attempt in {delay} seconds")
#                     await asyncio.sleep(delay)

#     async def get_channel(self) -> Channel:
#         async with self._connection_lock:
#             if not self.is_connected:
#                 await self.connect()
#             return self.channel

#     async def ensure_connection(self) -> None:
#         if not self.is_connected:
#             await self.connect()

#     async def close(self) -> None:
#         self._should_stop.set()
#         if self.connection and not self.connection.is_closed:
#             try:
#                 await self.connection.close()
#             except (asyncio.CancelledError, Exception) as e:
#                 if isinstance(e, asyncio.CancelledError):
#                     logger.warning("Connection close cancelled, forcing shutdown")
#                     raise
#                 logger.error(f"Error closing connection: {e}")
#             await asyncio.sleep(0.1)
#         self._is_connected.clear()

#     @property
#     def should_stop(self) -> asyncio.Event:
#         return self._should_stop

#     @property
#     def connected_event(self) -> asyncio.Event:
#         return self._is_connected


# class MessageValidator:
#     """Класс для валидации и подготовки входящих сообщений."""

#     @staticmethod
#     def validate(message: IncomingMessage) -> Dict[str, Any]:
#         try:
#             payload = json.loads(message.body.decode())
#             # Здесь можно добавить дополнительную валидацию полей
#             if "text" not in payload:
#                 raise ValueError("Missing 'text' field")
#             return payload
#         except Exception as e:
#             raise ValueError(f"Validation error: {e}") from e


# class MessageConsumer:
#     """
#     Класс для получения сообщений из очереди, формирования батчей и запуска их обработки.
#     Отделяет логику получения и формирования батчей от логики соединения.
#     """

#     def __init__(
#         self,
#         connection_manager: ConnectionManager,
#         config: Dict,
#         processor: BatchProcessor,
#     ):
#         self.connection_manager = connection_manager
#         self.config = config
#         self.processor = processor
#         self.pending_messages: List[Tuple[Dict, IncomingMessage]] = []
#         self._batch_lock = asyncio.Lock()
#         self.middleware = LoggingMiddleware(service_name="MessageConsumer")

#     async def setup_queues(self) -> None:
#         await self.connection_manager.ensure_connection()
#         # Объявляем входную очередь
#         await self.connection_manager.channel.declare_queue(
#             self.config["input_queue"],
#             durable=True,
#             arguments={"x-max-priority": 10, "x-queue-type": "classic"},
#         )
#         # Объявляем выходную очередь (для результатов) и очередь ошибок
#         await self.connection_manager.channel.declare_queue(
#             self.config["output_queue"],
#             durable=True,
#             arguments={"x-queue-type": "classic"},
#         )
#         await self.connection_manager.channel.declare_queue(
#             self.config["error_queue"],
#             durable=True,
#             arguments={"x-queue-type": "classic"},
#         )

#     async def handle_message(self, message: IncomingMessage) -> None:

#         @self.middleware.wrap_consumer
#         async def _inner_handler(message: IncomingMessage):
#             async with message.process():
#                 try:
#                     payload = MessageValidator.validate(message)
#                     # logger.info(f"Received message: {payload}")
#                     async with self._batch_lock:
#                         self.pending_messages.append((payload, message))
#                     if len(self.pending_messages) >= self.processor.batch_size:
#                         await self.process_batch()
#                 except Exception as e:
#                     # logger.error(f"Message processing error: {e}")
#                     await self.send_error(e, message)

#         await _inner_handler(message)

#     async def process_batch(self) -> None:
#         async with self._batch_lock:
#             if not self.pending_messages:
#                 return
#             batch = self.pending_messages[: self.processor.batch_size]
#             self.pending_messages = self.pending_messages[self.processor.batch_size :]
#         try:
#             texts = [msg["text"] for msg, _ in batch]
#             vectors = await self.processor.process_text(texts)
#             for (original_msg, message), vector in zip(batch, vectors):
#                 result = {
#                     "message_id": original_msg.get("message_id"),
#                     "vector": vector,
#                     "metadata": original_msg.get("metadata", {}),
#                 }
#                 await self.send_result(result, message.correlation_id)
#         except Exception as e:
#             logger.error(f"Batch processing failed: {e}")
#             for _, message in batch:
#                 await self.send_error(e, message)

#     async def send_result(self, result: Dict, correlation_id: str) -> None:
#         message = Message(
#             body=json.dumps(result).encode(),
#             correlation_id=correlation_id,
#             delivery_mode=2,  # устойчивое сообщение
#         )
#         await self.connection_manager.channel.default_exchange.publish(
#             message,
#             routing_key=self.config["output_queue"],
#         )

#     async def send_error(
#         self, error: Exception, original_message: IncomingMessage
#     ) -> None:
#         error_msg = {
#             "error": str(error),
#             "original_message": original_message.body.decode(),
#             "correlation_id": original_message.correlation_id,
#         }
#         message = Message(
#             body=json.dumps(error_msg).encode(),
#             delivery_mode=2,
#         )
#         await self.connection_manager.channel.default_exchange.publish(
#             message,
#             routing_key=self.config["error_queue"],
#         )

#     async def batch_scheduler(self) -> None:
#         """
#         Периодически запускает обработку оставшихся сообщений в батче,
#         если они накопились, но пока не достигли размера батча.
#         """
#         while not self.connection_manager.should_stop.is_set():
#             await asyncio.sleep(self.processor.max_wait)
#             if self.pending_messages:
#                 await self.process_batch()

#     async def start_consuming(self) -> None:
#         try:
#             channel = await self.connection_manager.get_channel()
#             queue = await channel.get_queue(self.config["input_queue"])
#             await queue.consume(self.handle_message)
#             logger.info("Started consuming messages")

#             while not self.connection_manager.should_stop.is_set():
#                 await asyncio.sleep(1)

#         except Exception as e:
#             logger.error(f"Consuming failed: {e}")
#             await self.connection_manager.close()
#             raise


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

    async def run(self) -> None:
        try:
            await self.connection_manager.connect()
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
        "input_queue": "text_processing",
        "output_queue": "vector_results",
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
