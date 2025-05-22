from pydantic import BaseModel
from typing import List


class TaskCreationResponse(BaseModel):
    task_id: str


class TaskInfoResponse(BaseModel):
    task_id: str
    status: str
    result: List[List[float]]
