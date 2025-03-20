from typing import Generator
from celery_sqlalchemy_scheduler.session import SessionManager
from travel_ai_backend.app.core.config import settings


def get_job_db() -> Generator:
    session_manager = SessionManager()
    engine, _session = session_manager.create_session(
        str(settings.SYNC_CELERY_BEAT_DATABASE_URI)
        # "db+postgresql://postgres:postgres@database:5432/celery_schedule_jobs"
    )

    with _session() as session:
        yield session
