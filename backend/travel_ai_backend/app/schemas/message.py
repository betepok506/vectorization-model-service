from pydantic import BaseModel, Extra
from typing import List, Dict, Any

class MessageSchema(BaseModel):
    """Модель для валидации входящих сообщений"""

    text: str
    message_id: str
    language: str = "en"
    metadata: Dict[str, Any] = {}
    
    class Config:
        extra = 'forbid'  # Запрет лишних полей
        json_schema_extra = {
            "example": {
                "text": "Пример текста",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "language": "ru",
                "metadata": {"source": "web"}
            }
        }