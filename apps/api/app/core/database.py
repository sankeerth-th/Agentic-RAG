from sqlalchemy import Engine, create_engine

from app.core.config import Settings

SCHEMA_REVISION = "0001"


def create_database_engine(settings: Settings) -> Engine:
    timeout = settings.dependency_timeout_seconds
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=timeout,
        connect_args={
            "connect_timeout": timeout,
            "options": f"-c statement_timeout={timeout * 1000}",
        },
        hide_parameters=True,
    )
