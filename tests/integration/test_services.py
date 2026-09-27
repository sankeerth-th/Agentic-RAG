import io
from uuid import uuid4

from fastapi.testclient import TestClient


def test_real_dependency_readiness_and_s3_stream_round_trip():
    from app.core.config import Settings
    from app.core.services import Services
    from app.main import create_app

    services = Services(Settings())
    key = f"smoke/{uuid4()}.txt"
    try:
        assert services.readiness() == {"postgres": True, "qdrant": True, "redis": True, "s3": True}
        services.storage.upload(key, io.BytesIO(b"source evidence"))
        output = io.BytesIO()
        services.storage.download(key, output)
        assert output.getvalue() == b"source evidence"
        with TestClient(create_app()) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/ready").status_code == 200
    finally:
        services.storage.client.delete_object(Bucket=services.storage.bucket, Key=key)
        services.close()


def test_missing_bucket_is_unready():
    from app.core.config import Settings
    from app.core.services import Services

    settings = Settings(s3_bucket=f"missing-{uuid4()}")
    services = Services(settings)
    try:
        checks = services.readiness()
        assert checks["s3"] is False
        assert checks["postgres"] is True
    finally:
        services.close()


def test_readiness_requires_migration_revision(monkeypatch):
    from app.core.config import Settings
    from app.core.services import Services

    services = Services(Settings())
    try:
        monkeypatch.setattr("app.core.services.SCHEMA_REVISION", "new-revision-required")
        assert services.readiness()["postgres"] is False
    finally:
        services.close()
