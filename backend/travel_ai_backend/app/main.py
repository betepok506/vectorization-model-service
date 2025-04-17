import gc
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI

from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from starlette.middleware.cors import CORSMiddleware
from travel_ai_backend.app.api.v1.api import api_router as api_router_v1
from travel_ai_backend.app.core.config import ModeEnum, settings
from travel_ai_backend.app.utils.fastapi_globals import GlobalsMiddleware, g
from travel_ai_backend.app.api.celery_task import CustomPipeline, MokeModel

# os.environ["HTTP_PROXY"] = "http://130.100.7.222:1082"
# os.environ["HTTPS_PROXY"] = "http://130.100.7.222:1082"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Load a pre-trained sentiment analysis model as a dictionary to an easy cleanup
    models: dict[str, Any] = {
        # "sentiment_model": CustomPipeline("Tochka-AI/ruRoPEBert-e5-base-2k")
        "sentiment_model": MokeModel("Tochka-AI/ruRoPEBert-e5-base-2k")
    }
    g.set_default("sentiment_model", models["sentiment_model"])
    print("startup fastapi")
    yield
    # shutdown
    models.clear()
    g.cleanup()
    gc.collect()


# Core Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URI),
    engine_args={
        "echo": False,
        "poolclass": (
            NullPool if settings.MODE == ModeEnum.testing else AsyncAdaptedQueuePool
        ),
        # "pool_pre_ping": True,
        # "pool_size": settings.POOL_SIZE,
        # "max_overflow": 64,
    },
)
app.add_middleware(GlobalsMiddleware)

# Set all CORS origins enabled
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class CustomException(Exception):
    http_code: int
    code: str
    message: str

    def __init__(
        self,
        http_code: int = 500,
        code: str | None = None,
        message: str = "This is an error message",
    ):
        self.http_code = http_code
        self.code = code if code else str(self.http_code)
        self.message = message


@app.get("/")
async def root():
    """
    An example "Hello world" FastAPI route.
    """
    # if oso.is_allowed(user, "read", message):
    return {"message": "Hello World"}


# Add Routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "travel_ai_backend.app.main:app", host="0.0.0.0", port=8000, reload=True
    )
