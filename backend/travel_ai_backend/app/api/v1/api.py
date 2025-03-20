from fastapi import APIRouter
from travel_ai_backend.app.api.v1.endpoints import (
    vectorization
)

api_router = APIRouter()
api_router.include_router(
    vectorization.router, prefix="/task", tags=["task"]
)
