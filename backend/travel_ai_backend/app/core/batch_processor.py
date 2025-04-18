import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
# from transformers import DistilBertTokenizer, DistilBertModel
from transformers import AutoModel, AutoTokenizer
import torch


class BatchProcessor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
        # self.model = DistilBertModel.from_pretrained("distilbert-base-uncased").to(
        #     self.device
        # )
        model_name = "Tochka-AI/ruRoPEBert-e5-base-2k"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name, trust_remote_code=True, attn_implementation="sdpa"
        ).to(
            self.device
        )
        
        self.model.eval()

        self.batch_size = 32  # Оптимальный размер батча для вашего железа
        self.max_wait = 0.1  # Максимальное время ожидания батча в секундах
        self.current_batch = []
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def process_text(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._process_sync, text)

    def _process_sync(self, texts: List[str]) -> List[float]:
        # inputs = self.tokenizer(
        #     text, return_tensors="pt", padding=True, truncation=True, max_length=512
        # ).to(self.device)

        # with torch.no_grad():
        #     outputs = self.model(**inputs)

        batch = self.tokenizer.batch_encode_plus(texts, return_tensors='pt', padding=True).to(self.device)
        with torch.inference_mode():
            outputs = self.model(**batch).pooler_output 
  
        return outputs.cpu().numpy().tolist()
