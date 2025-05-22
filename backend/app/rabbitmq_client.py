import aio_pika
import json
import logging
import asyncio
import time
from app.core.metrics import (
    RABBITMQ_RECONNECTS,
    RABBITMQ_CONNECTION_ERRORS,
    RABBITMQ_MESSAGE_PROCESS_TIME,
    RABBITMQ_MESSAGES_PUBLISHED,
    RABBITMQ_MESSAGES_RECEIVED,
)

logger = logging.getLogger("RabbitMQClient")


class RabbitMQClient:
    """Клиент для взаимодействия с RabbitMQ, поддерживающий переподключение и работу с очередями."""

    def __init__(self, url: str):
        """
        Инициализирует клиент RabbitMQ.
        """
        self.connection = None
        self.channel = None
        self.handlers = {}
        self._is_connecting = False
        self.exchanges = {}
        self.url = url

    async def connect(self, start_wait_time: int=1, max_wait_time:int =30):
        """
        Подключается к RabbitMQ с повторными попытками.

        Parameters
        ----------
        url : str
            URL подключения к RabbitMQ.
        """
        wait_time = start_wait_time
        while True:
            if self._is_connecting:
                return
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                logger.info("[+] Connected to RabbitMQ")
                self._is_connecting = True
                RABBITMQ_RECONNECTS.inc()
            except Exception as e:
                logger.error(f"[x] Connection failed: {e}")
                wait_time = min(wait_time, max_wait_time)
                logger.info(f"[x] Reconnecting in {wait_time} sec...")
                await asyncio.sleep(wait_time)
                self._is_connecting = False
                wait_time*=2

    async def close(self):
        """
        Корректно закрывает соединение с RabbitMQ.
        """
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("[x] RabbitMQ connection closed")

    async def declare_queue(self, queue_name: str, durable: bool = True):
        """
        Объявляет очередь в RabbitMQ с указанными параметрами.

        Parameters
        ----------
        queue_name : str
            Название очереди.
        durable : bool, optional
            Флаг устойчивости очереди (сохранение между перезапусками).
        priority : int, optional
            Приоритет очереди (x-max-priority), по умолчанию 10.

        Returns
        -------
        aio_pika.Queue
            Объект очереди.
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=durable)
        logger.info(f"[x] Declared queue '{queue_name}'")
        return queue

    async def publish(self, queue_name: str, message: dict):
        """
        Публикует сообщение в указанную очередь.

        Parameters
        ----------
        queue_name : str
            Название очереди.
        message : dict
            Сообщение для отправки.
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            exchange = self.channel.default_exchange
            await exchange.publish(
                aio_pika.Message(
                    body=message_json.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )
            RABBITMQ_MESSAGES_PUBLISHED.inc()
            logger.debug(f"[x] Sent to {queue_name}")
        except Exception as e:
            RABBITMQ_CONNECTION_ERRORS.inc()
            logger.error(f"[!] Error sending message: {e}")
        # finally:
        #     CURRENT_CHUNKS.dec()

    def register_handler(self, queue_name: str, handler: callable):
        """
        Регистрирует обработчик для указанной очереди.

        Parameters
        ----------
        queue_name : str
            Название очереди.
        handler : callable
            Асинхронная функция-обработчик.
        """
        self.handlers[queue_name] = handler

    async def declare_exchange(
        self,
        exchange_name: str,
        type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
    ):
        """Создает exchange, если его нет"""
        if not self.connection or self.connection.is_closed:
            await self.connect()

        if exchange_name in self.exchanges:
            return self.exchanges[exchange_name]

        exchange = await self.channel.declare_exchange(
            exchange_name, type, durable=True
        )
        self.exchanges[exchange_name] = exchange
        logger.info(f"[x] Declared exchange '{exchange_name}'")
        return exchange

    async def consume(self, queue_name: str):
        """
        Запускает потребителя для указанной очереди.

        Parameters
        ----------
        queue_name : str
            Название очереди, из которой будут читаться сообщения.
        """
        while True:
            if not self.connection or self.connection.is_closed:
                logger.warning(f"[x] Очередь {queue_name}: соединение закрыто, ждём восстановления...")
                await asyncio.sleep(5)
                continue

            try:
                queue = await self.channel.get_queue(queue_name)
            except Exception:
                queue = await self.declare_queue(queue_name)

            async with queue.iterator() as qiter:
                async for message in qiter:
                    # Увеличиваем счетчик обработанных сообщений
                    RABBITMQ_MESSAGES_RECEIVED.inc()
                    async with message.process():
                        if queue_name in self.handlers:
                            data = json.loads(message.body.decode())
                            start = time.time()
                            await self.handlers[queue_name](data)
                            elapsed = time.time() - start
                            RABBITMQ_MESSAGE_PROCESS_TIME.observe(elapsed)
                        else:
                            logger.warning(
                                f"[!] No handler registered for queue: {queue_name}"
                            )

    async def start_consumers(self):
        """
        Запускает всех потребителей для зарегистрированных очередей.
        """
        for queue_name in self.handlers.keys():
            asyncio.create_task(self.consume(queue_name))
