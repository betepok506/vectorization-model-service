from prometheus_client import start_http_server, Counter, Histogram, Gauge
import logging

logger = logging.getLogger("MetricsServer")

# --- Метрики ---
VECTORIZE_REQUESTS = Counter(
    "vectorize_requests_total",
    "Total number of vectorization requests processed"
)

VECTORIZE_ERRORS = Counter(
    "vectorize_errors_total",
    "Total number of errors during vectorization"
)

VECTORIZE_LATENCY = Histogram(
    "vectorize_latency_seconds",
    "Time taken to process a batch of texts",
    buckets=(0.1, 0.2, 0.5, 1.0, 2.0, 5.0, '+Inf')
)

VECTORIZE_BATCH_SIZE = Gauge(
    "vectorize_batch_size",
    "Current size of the batch being processed"
)

VECTORIZE_EMBEDDING_DIM = Gauge(
    "vectorize_embeddings_dim",
    "Dimension of generated embeddings"
)

# --- Метрики RabbitMQ ---
RABBITMQ_MESSAGES_RECEIVED = Counter(
    "rabbitmq_messages_received_total",
    "Total number of messages received from RabbitMQ"
)

RABBITMQ_MESSAGES_PUBLISHED = Counter(
    "rabbitmq_messages_published_total",
    "Total number of messages published to RabbitMQ"
)

RABBITMQ_MESSAGE_PROCESS_TIME = Histogram(
    "rabbitmq_message_process_time_seconds",
    "Time taken to process a single message from queue"
)

RABBITMQ_CONNECTION_ERRORS = Counter(
    "rabbitmq_connection_errors_total",
    "Number of RabbitMQ connection errors"
)

RABBITMQ_RECONNECTS = Counter(
    "rabbitmq_reconnects_total",
    "Number of successful reconnects to RabbitMQ"
)

def start_metrics_server(port=8000):
    """
    Запускает HTTP-сервер с экспортом метрик Prometheus.

    Parameters
    ----------
    port : int, optional
        Порт, на котором будет запущен сервер.
    """
    logger.info(f"Starting metrics server on port {port}")
    start_http_server(port)
    logger.info("Prometheus metrics server is running")