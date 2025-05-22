# Запуск сервера Fast Api

Запуск сервера осуществляется из консоли внутри devcontainer. Команда:
```
gunicorn -w 1 -k uvicorn.workers.UvicornWorker travel_ai_backend.app.main:app  --bind 0.0.0.0:8000 --preload --log-level=debug --timeout 120
```

Метрики `Prometheus` доступны по адрессу:
```
http://<URI>:<PORT>/metrics
```

Лог успешного запуска сервиса:
```
{"timestamp": "2025-05-22 08:25:18,168", "level": "INFO", "logger": "MetricsServer", "message": "Starting metrics server on port 8000"}
{"timestamp": "2025-05-22 08:25:18,179", "level": "INFO", "logger": "MetricsServer", "message": "Prometheus metrics server is running"}
{"timestamp": "2025-05-22 08:25:26,912", "level": "INFO", "logger": "RabbitMQClient", "message": "[+] Connected to RabbitMQ"}
{"timestamp": "2025-05-22 08:25:26,913", "level": "INFO", "logger": "services.vectorization_service", "message": "Service started"}
```