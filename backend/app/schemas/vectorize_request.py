from pydantic import BaseModel, Extra
from typing import List, Dict, Any


class VectorizeRequestSchema(BaseModel):
    """
    Схема данных для запроса векторизации.

    Attributes
    ----------
    message_id : str
        Уникальный идентификатор запроса.
    text : str
        Текст для векторизации.
    callback_queue : str
        Имя очереди, в которую будет отправлен результат.
    metadata : dict, optional
        Дополнительные данные запроса.
    """

    message_id: str
    text: str
    callback_queue: str
    metadata: Dict[str, Any] = {}

    class Config:
        extra = "forbid"  # Запрет лишних полей
        json_schema_extra = {
            "example": {
                "text": "Пример текста",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "callback_queue": "prompt_generator_embeddings",
                "metadata": {"source": "web"},
            }
        }
