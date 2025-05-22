# Описание

Микросервис векторизации текстов на основе нейросетевых моделей из библиотеки HuggingFace Transformers.
Сервис принимает текстовые сообщения через RabbitMQ , обрабатывает их пакетами и отправляет результаты в указанную очередь.

### 📌 Основные возможности:
- ✅ Асинхронная обработка текстов
- 📦 Поддержка батчинга (настраиваемый размер батча)
- 🔄 Автоматическое переподключение к RabbitMQ
- 📊 Метрики Prometheus для мониторинга
- 🔁 Поддержка callback-очередей
- 🧾 Валидация входящих данных через Pydantic

### 🛠 Технологии:
- Python 3.10+
- aio_pika
- Pydantic
- Transformers + Torch
- Prometheus Client
- Logging

## Структура проекта

Актуализировать и расписать
```
vectorization-model-service/
.
├── .env # Файл с переменными окружения для конфигурации сервиса
├── Dockerfile
├── Makefile
├── README.md 
├── app
│   ├── __init__.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py   # Конфигурация сервиса
│   │   └── metrics.py  # Собираемые метрики
│   ├── logger.py  # Логгер
│   ├── main.py # Точка входа в программу
│   ├── models
│   │   └── batch_processor.py
│   ├── rabbitmq_client.py # Клиент для работы с RabbitMQ
│   ├── schemas # Схемы данных
│   │   ├── response_schema.py
│   │   └── vectorize_request.py
│   └── services # Основная логика сервиса
│       └── vectorization_service.py
├── deployment.md
├── development.md
├── poetry.lock
├── pyproject.toml
└── tests # Тесты проекта
```

# Запуск

Перед запуском проекта необходимо создать файл `.env` и задать переменные окружения

### Переменные окружения

|Переменная|По умолчанию|Описание
|----------|----------|----------|
|**RABBITMQ_URI**|amqp://guest:guest@rabbitmq/|URL подключения к RabbitMQ|
|**VECTORIZE_MODEL**|Tochka-AI/ruRoPEBert-e5-base-2k|Модель для векторизации|
|**BATCH_SIZE**|32|Максимальное количество текстов в одном батче|
|**MAX_WAIT**|0.1|Время ожидания перед отправкой частичного батча (в секундах)
|**LOG_LEVEL**|INFO|Уровень логирования (DEBUG, INFO, WARNING)|

Сборка и запуск сервиса:
```
docker-compose up --build
```

Остановка сервиса:
```
docker-compose down
```

## Метрики

|Название|Тип|Единица измерения|Описание|
|-----------------|-----------------|-----------------|-----------------|
|**vectorize_requests_total**|Counter|шт.|Общее количество обработанных запросов на векторизацию|
|**vectorize_errors_total**|Counter|шт.|Количество ошибок при векторизации (валидация, модель и т.д.)|
|**vectorize_latency_seconds**|Histogram|секунды|Время обработки одного батча текстов|
|**vectorize_batch_size**|Gauge|шт.|Размер текущего батча перед отправкой на обработку|
|**vectorize_embeddings_dim**|Gauge|шт.|Размерность эмбеддингов (например, 768 для BERT)|
|**rabbitmq_messages_received_total**|Counter|шт.|Количество сообщений, полученных из RabbitMQ|
|**rabbitmq_messages_published_total**|Counter|шт.|Количество сообщений, отправленных в очередь RabbitMQ|
|**rabbitmq_message_process_time_seconds**|Histogram|секунды|Время обработки одного сообщения от получения до отправки ответа|
|**rabbitmq_connection_errors_total**|Counter|шт.|Число ошибок подключения к RabbitMQ|
|**rabbitmq_reconnects_total**|Counter|шт.|Количество успешных переподключений к RabbitMQ|

Для получения метрик сервиса:
```
scrape_configs:
  - job_name: 'vectorize-service'
    static_configs:
      - targets: ['vectorization-model:8000']
```


## Пример сообщения

```
{
  "message_id": "abc123",
  "text": "Как зарегистрироваться?",
  "callback_queue": "prompt_generator_embeddings",
  "metadata": {
    "source": "web"
  }
}
```