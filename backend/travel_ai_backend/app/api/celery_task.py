
import time
from travel_ai_backend.app.core.celery import celery
import logging
from celery import Task
from transformers import AutoModel, AutoTokenizer
import torch
from typing import List
import numpy as np

class MokeModel:
    def __init__(self, *args, **kwds):
        pass

    def __call__(self, *args, **kwds):
        rng1 = np.random.default_rng()
        rng1.random() 
        return [rng1.random()] * 768

class CustomPipeline:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name, trust_remote_code=True, attn_implementation="eager"
        )

    def __call__(self, texts: List[str]):
        test_batch = self.tokenizer.batch_encode_plus(
            ["Привет, чем занят?", "Здравствуйте, чем вы занимаетесь?"],
            return_tensors="pt",
            padding=True,
        )
        with torch.inference_mode():
            pooled_output = self.model(**test_batch).pooler_output

        return pooled_output


class PredictTransformersPipelineTask(Task):
    """
    Abstraction of Celery's Task class to support loading transformers model.
    """

    task_name = ""
    model_name = ""
    tokenizer_name = ""
    abstract = True

    def __init__(self):
        super().__init__()
        self.pipeline = None

    def __call__(self, *args, **kwargs):
        """
        Load pipeline on first call (i.e. first task processed)
        Avoids the need to load pipeline on each task request
        """
        if not self.pipeline:
            logging.info("Loading pipeline...")
            # self.pipeline = CustomPipeline(self.model_name)
            self.pipeline = MokeModel(self.model_name)
            logging.info("Pipeline loaded")
        return self.run(*args, **kwargs)


@celery.task(
    ignore_result=False,
    bind=True,
    base=PredictTransformersPipelineTask,
    task_name="feature-extraction",
    model_name="Tochka-AI/ruRoPEBert-e5-base-2k",
    tokenizer_name="Tochka-AI/ruRoPEBert-e5-base-2k",
    name="tasks.predict_transformers_pipeline",
)
def predict_transformers_pipeline(self, prompt: str):
    """
    Essentially the run method of PredictTask
    """
    result = self.pipeline(prompt)
    return result


@celery.task(name="tasks.increment")
def increment(value: int) -> int:
    time.sleep(4)
    new_value = value + 1
    return new_value
