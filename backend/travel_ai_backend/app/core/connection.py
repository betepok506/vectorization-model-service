import asyncio
import logging
from aio_pika import (
    connect,
    RobustConnection,
    Channel,
)
from aio_pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Класс для управления соединением и переподключением к RabbitMQ."""

    def __init__(
        self,
        rabbitmq_url: str,
        max_reconnect_attempts: int = 10,
        reconnect_delay: int = 5,
    ):
        self.rabbitmq_url = rabbitmq_url
        self._max_reconnect_attempts = max_reconnect_attempts
        self._base_delay = reconnect_delay

        self.connection: RobustConnection = None
        self.channel: Channel = None
        # Событие, которое сигнализирует об успешно установленном подключении
        self._is_connected = asyncio.Event()
        self._should_stop = asyncio.Event()

        self._connection_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return (
            self._is_connected.is_set()
            and self.connection
            and not self.connection.is_closed
        )

    async def connect(self) -> None:
        async with self._connection_lock:
            attempts = 0
            while not self._should_stop.is_set():
                try:
                    self.connection = await connect(
                        self.rabbitmq_url,
                        timeout=10,
                        client_properties={"connection_name": "vectorization_service"},
                    )
                    self.channel = await self.connection.channel()
                    # Пример установки QoS – значение можно сделать параметризуемым
                    await self.channel.set_qos(prefetch_count=100)
                    self._is_connected.set()
                    logger.info("Successfully connected to RabbitMQ")
                    return
                except (AMQPConnectionError, ConnectionError, OSError) as e:
                    attempts += 1
                    logger.error(f"Connection attempt {attempts} failed: {str(e)}")
                    if attempts >= self._max_reconnect_attempts:
                        logger.error("Max reconnect attempts reached. Exiting...")
                        self._should_stop.set()
                        raise e
                    delay = self._base_delay * attempts
                    logger.info(f"Next connection attempt in {delay} seconds")
                    await asyncio.sleep(delay)

    async def get_channel(self) -> Channel:
        async with self._connection_lock:
            if not self.is_connected:
                await self.connect()
            return self.channel

    async def ensure_connection(self) -> None:
        if not self.is_connected:
            await self.connect()

    async def close(self) -> None:
        self._should_stop.set()
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
            except (asyncio.CancelledError, Exception) as e:
                if isinstance(e, asyncio.CancelledError):
                    logger.warning("Connection close cancelled, forcing shutdown")
                    raise
                logger.error(f"Error closing connection: {e}")
            await asyncio.sleep(0.1)
        self._is_connected.clear()

    @property
    def should_stop(self) -> asyncio.Event:
        return self._should_stop

    @property
    def connected_event(self) -> asyncio.Event:
        return self._is_connected
