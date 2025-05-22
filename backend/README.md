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

## Структура проекта

Актуализировать и расписать
```
vectorization-service/
├── main.py                      # Точка входа
├── config.py                    # Конфигурация
├── schemas/
│   └── vectorize_request.py   # Схема входящих данных
├── models/
│   └── batch_processor.py     # Пакетная обработка текстов
├── rabbitmq_client.py         # Клиент RabbitMQ
└── services/
    └── vectorization_service.py # Логика сервиса
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

## Переменные окружения

|Переменная|По умолчанию|Описание
|----------|----------|----------|
|**RABBITMQ_URI**|amqp://guest:guest@rabbitmq/|URL подключения к RabbitMQ|
|**VECTORIZE_MODEL**|Tochka-AI/ruRoPEBert-e5-base-2k|Модель для векторизации|
|**BATCH_SIZE**|32|Максимальное количество текстов в одном батче|
|**MAX_WAIT**|0.1|Время ожидания перед отправкой частичного батча (в секундах)
|**LOG_LEVEL**|INFO|Уровень логирования (DEBUG, INFO, WARNING)|