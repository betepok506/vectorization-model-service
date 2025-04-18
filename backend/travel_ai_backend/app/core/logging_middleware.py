import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Callable, Awaitable
from aio_pika import IncomingMessage
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def log_message(self, message: Dict, context: Dict):
        log_data = {
            "service": self.service_name,
            "message_id": context.get("correlation_id"),
            "queue": context.get("queue"),
            "action": context.get("action"),
            "processing_time": context.get("processing_time"),
            "status": context.get("status"),
            "error": context.get("error"),
            "retry_count": context.get("retry_count"),
            "timestamp": time.time(),
        }

        if context["status"] == "error":
            logger.error(log_data)
        else:
            logger.info(log_data)

    @asynccontextmanager
    async def message_context(self, message: IncomingMessage, queue: str):
        start_time = time.monotonic()
        context = {
            "correlation_id": message.message_id,
            "queue": queue,
            "action": "process_message",
            "retry_count": message.headers.get("retry_count", 0),
        }

        try:
            yield context
            context.update(
                {"status": "success", "processing_time": time.monotonic() - start_time}
            )
        except Exception as e:
            context.update(
                {
                    "status": "error",
                    "error": str(e),
                    "processing_time": time.monotonic() - start_time,
                }
            )
            raise
        finally:
            await self.log_message(message, context)

    def wrap_consumer(self, handler: Callable[[Any], Awaitable[None]]):
        @wraps(handler)
        async def wrapped(message: IncomingMessage):
            async with self.message_context(
                message=message, queue=message.routing_key
            ) as context:
                result = await handler(message)
                context["result"] = result
                return result

        return wrapped

    def wrap_task(self, task_func: Callable):
        @wraps(task_func)
        async def wrapped(*args, **kwargs):
            start_time = time.monotonic()
            context = {
                "task": task_func.__name__,
                "args": args,
                "kwargs": kwargs,
                "status": "started",
            }
            logger.info(context)

            try:
                result = await task_func(*args, **kwargs)
                context.update(
                    {
                        "status": "success",
                        "processing_time": time.monotonic() - start_time,
                        "result": result,
                    }
                )
                logger.info(context)
                return result
            except Exception as e:
                context.update(
                    {
                        "status": "error",
                        "error": str(e),
                        "processing_time": time.monotonic() - start_time,
                    }
                )
                logger.error(context)
                raise

        return wrapped
