import logging
from collections.abc import Callable
from typing import Any, BinaryIO

import boto3
from botocore.config import Config
from fastapi import Request
from qdrant_client import QdrantClient
from redis import Redis
from sqlalchemy import text

from app.core.config import Settings
from app.core.database import SCHEMA_REVISION, create_database_engine

logger = logging.getLogger("rag.api")


class ObjectStorage:
    def __init__(self, client: Any, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    def check(self) -> None:
        self.client.head_bucket(Bucket=self.bucket)

    def upload(self, key: str, stream: BinaryIO) -> None:
        self.client.upload_fileobj(stream, self.bucket, key)

    def download(self, key: str, stream: BinaryIO) -> None:
        self.client.download_fileobj(self.bucket, key, stream)


class Services:
    def __init__(self, settings: Settings) -> None:
        timeout = settings.dependency_timeout_seconds
        self.database = create_database_engine(settings)
        self.qdrant = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None,
            timeout=timeout,
            check_compatibility=False,
        )
        self.redis = Redis.from_url(
            settings.redis_url.get_secret_value(),
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            retry_on_timeout=False,
        )
        self.storage = ObjectStorage(
            boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                region_name=settings.s3_region,
                aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
                aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
                config=Config(
                    connect_timeout=timeout,
                    read_timeout=timeout,
                    retries={"total_max_attempts": 1},
                    s3={"addressing_style": "path"},
                ),
            ),
            settings.s3_bucket,
        )

    def check_database(self) -> None:
        with self.database.connect() as connection:
            revisions = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalars()
            if list(revisions) != [SCHEMA_REVISION]:
                raise RuntimeError("database migration required")

    def readiness(self) -> dict[str, bool]:
        probes: dict[str, Callable[[], Any]] = {
            "postgres": self.check_database,
            "qdrant": self.qdrant.get_collections,
            "redis": self.redis.ping,
            "s3": self.storage.check,
        }
        result = {}
        for name, probe in probes.items():
            try:
                probe()
                result[name] = True
            except Exception:
                result[name] = False
                logger.warning("dependency_unavailable", extra={"dependency": name})
        return result

    def close(self) -> None:
        self.database.dispose()
        self.qdrant.close()
        self.redis.close()
        self.storage.client.close()


def get_services(request: Request) -> Services:
    return request.app.state.services
