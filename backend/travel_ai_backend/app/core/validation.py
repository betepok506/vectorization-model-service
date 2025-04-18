from aio_pika import (
    IncomingMessage
)
import json
from typing import Dict, Any
from travel_ai_backend.app.schemas.message import MessageSchema

class MessageValidator:
    """Класс для валидации и подготовки входящих сообщений."""

    @staticmethod
    def validate(message: IncomingMessage) -> Dict[str, Any]:
        try:
            payload = json.loads(message.body.decode())
            validated_data = MessageSchema(**payload)
            return validated_data
        except Exception as e:
            raise ValueError(f"Validation error: {e}") from e
