from fastapi import APIRouter, Depends, HTTPException
from travel_ai_backend.app.api.celery_task import predict_transformers_pipeline
from travel_ai_backend.app.schemas.response_schema import (
    IPostResponseBase,
    create_response,
)
from travel_ai_backend.app.core.celery import celery
from travel_ai_backend.app.schemas.task_schema import (
    TaskCreationResponse,
    TaskInfoResponse,
)
from typing import List

router = APIRouter()


@router.post(
    "/text-vectorization",
)
async def text_generation_prediction_batch_task(
    text: List[str] = ["Batman is awesome because"],
) -> IPostResponseBase[TaskCreationResponse]:
    """
    Async batch task for text generation using a NLP model from transformers libray
    """
    prection_task = predict_transformers_pipeline.delay(text)
    return create_response(data=TaskCreationResponse(task_id=prection_task.task_id))


@router.get(
    "/result",
)
async def get_result_from_batch_task(task_id: str) -> IPostResponseBase:
    """
    Get result from task using task_id
    """
    async_result = celery.AsyncResult(task_id)
    # print(f'result {async_result.get()}')
    if async_result.ready():
        print(f"Ready!!")
        if not async_result.successful():
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} with state {async_result.state}.",
            )

        result = async_result.get(timeout=1.0)
        return create_response(
            message="The task is completed!",
            data=TaskInfoResponse(task_id=task_id, result=result, status="Сompleted"),
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} does not exist or is still running.",
        )
