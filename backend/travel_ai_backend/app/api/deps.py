from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession
from travel_ai_backend.app.core.config import settings
from travel_ai_backend.app.db.session import SessionLocal, SessionLocalCelery

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_redis_client() -> Redis:
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
    return redis


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_jobs_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocalCelery() as session:
        yield session


