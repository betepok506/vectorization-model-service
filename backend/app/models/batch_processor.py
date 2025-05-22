import os
import asyncio
import torch
from transformers import AutoTokenizer, AutoModel
from typing import List
from app.core.metrics import (
    VECTORIZE_LATENCY,
    VECTORIZE_BATCH_SIZE,
    VECTORIZE_EMBEDDING_DIM,
    VECTORIZE_REQUESTS,
    VECTORIZE_ERRORS,
)
import logging

logger = logging.getLogger("BatchProcessor")


class BatchProcessor:
    """Класс для пакетной обработки текстов с помощью нейросетевой модели."""

    def __init__(self, model_name: str = "Tochka-AI/ruRoPEBert-e5-base-2k"):
        """
        Инициализирует объект BatchProcessor.

        Parameters
        ----------
        model_name : str, optional
            Название модели HuggingFace для векторизации, по умолчанию 'Tochka-AI/ruRoPEBert-e5-base-2k'
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(
            self.device
        )
        self.model.eval()

        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        self.max_wait = float(os.getenv("MAX_WAIT", "0.1"))  # в секундах

        self.current_batch = []
        self.lock = asyncio.Lock()
        self.timer = None

    async def add_to_batch(self, item: dict) -> None:
        """
        Добавляет элемент в текущий батч и запускает обработку при достижении batch_size.

        Parameters
        ----------
        item : dict
            Словарь с полями:
            - text: входной текст
            - message_id: уникальный ID сообщения
            - callback: функция обратного вызова для отправки результата
        """
        async with self.lock:
            self.current_batch.append(item)

        if len(self.current_batch) >= self.batch_size:
            await self.process_batch()

        elif self.timer is None:
            self.timer = asyncio.create_task(self._wait_and_process())

    async def _wait_and_process(self):
        """
        Ожидает `max_wait` секунд и запускает обработку частичного батча.
        """
        try:
            await asyncio.sleep(self.max_wait)
            await self.process_batch()
        except asyncio.CancelledError:
            pass

    def _process_sync(self, texts: List[str]) -> List[float]:
        """
        Обрабатывает список текстов и возвращает эмбеддинги.

        Parameters
        ----------
        texts : list of str
            Список текстовых строк для векторизации.

        Returns
        -------
        list of list of float
            Список эмбеддингов (векторных представлений текстов).
        """
        batch = self.tokenizer.batch_encode_plus(
            texts, return_tensors="pt", padding=True
        ).to(self.device)
        with torch.inference_mode():
            outputs = self.model(**batch).pooler_output

        return outputs.cpu().numpy().tolist()

    @VECTORIZE_LATENCY.time()
    async def process_batch(self):
        """
        Обрабатывает текущий батч текстов и отправляет результаты через callback.
        """
        async with self.lock:
            batch = self.current_batch[:]
            self.current_batch.clear()
            self.timer = None

        if not batch:
            return

        texts = [item["text"] for item in batch]
        try:
            embeddings = self._process_sync(texts)

            VECTORIZE_REQUESTS.inc(len(embeddings))
            VECTORIZE_BATCH_SIZE.set(0)
            
            # Проверяем, было ли уже установлено значение
            current_dim_value = VECTORIZE_EMBEDDING_DIM._value.get()

            if current_dim_value == 0 or current_dim_value is None:
                VECTORIZE_EMBEDDING_DIM.set(len(embeddings[0]))
                
            for item, embedding in zip(batch, embeddings):
                result = {
                    "message_id": item["message_id"],
                    "embedding": embedding,
                    "metadata": item.get("metadata", None),
                }
                await item["callback"](result)
        except Exception as e:
            logger.error(f"Error during batch processing: {e}")
            VECTORIZE_ERRORS.inc(len(batch))
