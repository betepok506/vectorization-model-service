import logging
import json
from typing import Optional

try:
    import colorlog
except ImportError:
    colorlog = None

class ContextFilter(logging.Filter):
    """
    Фильтр для добавления контекста в каждый лог.
    """

    def filter(self, record):
        record.message_id = getattr(record, 'message_id', 'no-id')
        record.queue_name = getattr(record, 'queue_name', 'no-queue')
        return True


class JsonLogFormatter(logging.Formatter):
    """Форматтер в JSON"""

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            # "message_id": getattr(record, "message_id", None),
            # "queue_name": getattr(record, "queue_name", None),
        }
        # Добавляем extra-поля, если они есть
        for key, value in getattr(record, "context", {}).items():
            log_data[key] = value
        return json.dumps(log_data)

class ColorLogFormatter:
    """Цветной форматтер для development-среды"""

    @staticmethod
    def get_formatter():
        if colorlog is None:
            return logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

        formatter = colorlog.ColoredFormatter(
            "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        return formatter

def setup_logger(level=logging.INFO, json_format=False):
    """
    Настройка глобального логгера (вызывается один раз при старте сервиса)

    Parameters
    ----------
    level : int
        Уровень логирования
    json_format : bool
        Использовать JSON-формат логов
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Очищаем старые хендлеры
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Создаем новый хендлер
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Выбираем формат
    if json_format:
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Добавляем фильтр
    root_logger.addFilter(ContextFilter())

    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)

    return root_logger