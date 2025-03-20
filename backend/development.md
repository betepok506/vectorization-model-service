# Запуск сервера Fast Api

Запуск сервера осуществляется из консоли внутри devcontainer. Команда:
```
gunicorn -w 3 -k uvicorn.workers.UvicornWorker travel_ai_backend.app.main:app  --bind 0.0.0.0:8000 --preload --log-level=debug --timeout 120
```