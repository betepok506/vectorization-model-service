import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


# RabbitMQ
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://admin:secret@130.100.7.137:5672/")

# Модель
MODEL_NAME = os.getenv("VECTORIZE_MODEL", "Tochka-AI/ruRoPEBert-e5-base-2k")
INPUT_QUEUE = os.getenv("INPUT_QUEUE", "vectorize_queue")
# Батч
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
MAX_WAIT = float(os.getenv("MAX_WAIT", "0.1"))

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_JSON_FORMAT = os.getenv("LOG_JSON_FORMAT", "True")

class Settings(BaseSettings):
    MODE: ModeEnum = ModeEnum.development
    
    PROJECT_NAME: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 1  # 1 hour
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 100  # 100 days

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=os.path.join(os.getcwd(), ".env")
    )


settings = Settings()
