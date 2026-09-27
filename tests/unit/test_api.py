import io
import json
import logging
from unittest.mock import Mock

from fastapi.testclient import TestClient


def test_health_does_not_depend_on_external_services():
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_readiness_is_503_for_any_required_dependency_failure():
    from app.core.services import get_services
    from app.main import create_app

    application = create_app()
    checks = {"postgres": True, "qdrant": True, "redis": True, "s3": True}
    fake = Mock()
    application.dependency_overrides[get_services] = lambda: fake
    with TestClient(application) as client:
        fake.readiness.return_value = checks
        assert client.get("/ready").status_code == 200
        for dependency in checks:
            fake.readiness.return_value = checks | {dependency: False}
            response = client.get("/ready")
            assert response.status_code == 503
            assert response.json()["dependencies"][dependency] == "unavailable"


def test_unexpected_errors_have_request_ids_but_no_exception_secrets():
    from app.main import create_app

    application = create_app()

    @application.get("/explode")
    def explode():
        raise RuntimeError("secret-value-that-must-not-leak")

    with TestClient(application, raise_server_exceptions=False) as client:
        result = client.get("/explode", headers={"x-request-id": "untrusted-content"})
        missing = client.get("/missing")
    assert result.status_code == 500
    assert "secret-value" not in result.text
    assert result.json()["error"]["code"] == "internal_error"
    assert result.headers["x-request-id"] == result.json()["request_id"]
    assert result.json()["request_id"] != "untrusted-content"
    assert missing.json()["error"]["code"] == "not_found"


def test_validation_errors_do_not_echo_input():
    from app.main import create_app
    from rag_contracts.retrieval import RetrievalRequest

    application = create_app()

    @application.post("/validate")
    def validate(payload: RetrievalRequest):
        return payload

    with TestClient(application) as client:
        result = client.post("/validate", json={"unexpected": "secret-value"})
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "validation_error"
    assert "secret-value" not in result.text


def test_log_formatter_only_serializes_allowlisted_fields():
    from app.core.logging import JsonFormatter

    record = logging.LogRecord("rag.api", logging.ERROR, __file__, 1, "request_failed", (), None)
    record.request_id = "request-1"
    record.secret = "secret-value"
    record.exc_info = (ValueError, ValueError("exception-secret"), None)
    output = JsonFormatter().format(record)
    assert json.loads(output)["event"] == "request_failed"
    assert "secret" not in output


def test_settings_and_object_storage_use_explicit_configuration():
    from app.core.config import Settings
    from app.core.services import ObjectStorage

    settings = Settings(_env_file=None)
    assert "local-rag-password" not in repr(settings)
    client = Mock()
    storage = ObjectStorage(client, "corpus")
    stream = io.BytesIO(b"evidence")
    storage.upload("document.txt", stream)
    client.upload_fileobj.assert_called_once_with(stream, "corpus", "document.txt")


def test_worker_uses_json_only_and_does_not_use_redis_as_result_store():
    from ingestion_worker.app import create_worker

    worker = create_worker()
    assert worker.conf.accept_content == ["json"]
    assert worker.conf.result_backend is None
    assert worker.conf.worker_prefetch_multiplier == 1
    assert worker.conf.task_default_queue == "ingestion"
