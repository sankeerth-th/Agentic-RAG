from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://rag:local-rag-password@127.0.0.1:55432/rag"
    )
    redis_url: SecretStr = SecretStr("redis://127.0.0.1:56379/0")
    qdrant_url: str = "http://127.0.0.1:56333"
    qdrant_api_key: SecretStr | None = None
    s3_endpoint_url: str = "http://127.0.0.1:59000"
    s3_access_key_id: SecretStr = SecretStr("local-rag-user")
    s3_secret_access_key: SecretStr = SecretStr("local-rag-password")
    s3_bucket: str = "rag-sources"
    s3_region: str = "us-east-1"
    dependency_timeout_seconds: int = Field(default=2, ge=1, le=10)
