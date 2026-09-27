import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in ("request_id", "method", "status", "duration_ms", "dependency"):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data, allow_nan=False)


def configure_logging() -> None:
    logger = logging.getLogger("rag.api")
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
