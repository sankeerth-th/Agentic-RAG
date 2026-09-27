"""PostgreSQL metadata; published snapshot rows are protected by migration triggers."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


def identity() -> list[Column]:
    return [
        Column("id", Uuid, primary_key=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ]


def state() -> list:
    return [
        Column("status", String(16), nullable=False),
        CheckConstraint(
            "status IN ('queued','running','completed','failed','cancelled')", name="valid_status"
        ),
        Column("started_at", DateTime(timezone=True)),
        Column("finished_at", DateTime(timezone=True)),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name="time_order",
        ),
        Column("error", JSONB),
    ]


datasets = Table(
    "datasets",
    metadata,
    *identity(),
    Column("name", Text, nullable=False),
    Column("description", Text),
    CheckConstraint("length(btrim(name)) > 0", name="name_not_empty"),
)
index_profiles = Table(
    "index_profiles",
    metadata,
    *identity(),
    Column("name", Text, nullable=False),
    Column("configuration", JSONB, nullable=False),
    CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_object"),
)
dataset_versions = Table(
    "dataset_versions",
    metadata,
    *identity(),
    Column("dataset_id", Uuid, ForeignKey("datasets.id"), nullable=False),
    Column("index_profile_id", Uuid, ForeignKey("index_profiles.id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("document_manifest_uri", Text, nullable=False),
    Column("configuration", JSONB, nullable=False),
    UniqueConstraint("dataset_id", "version"),
    UniqueConstraint("id", "dataset_id", name="uq_dataset_versions_dataset"),
    UniqueConstraint("id", "dataset_id", "index_profile_id", name="uq_dataset_versions_profile"),
    CheckConstraint("version >= 1", name="positive_version"),
    CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
    CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_object"),
)
documents = Table(
    "documents",
    metadata,
    *identity(),
    Column("dataset_id", Uuid, nullable=False),
    Column("dataset_version_id", Uuid, nullable=False),
    Column("source", JSONB, nullable=False),
    Column("title", Text, nullable=False),
    Column("object_key", Text, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("byte_size", BigInteger, nullable=False),
    ForeignKeyConstraint(
        ["dataset_version_id", "dataset_id"], ["dataset_versions.id", "dataset_versions.dataset_id"]
    ),
    UniqueConstraint("id", "dataset_version_id", "dataset_id", name="uq_documents_provenance"),
    UniqueConstraint("dataset_version_id", "object_key", name="uq_documents_version_object"),
    CheckConstraint("byte_size >= 0", name="nonnegative_size"),
    CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
    CheckConstraint("jsonb_typeof(source) = 'object'", name="source_object"),
)
chunks = Table(
    "chunks",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("document_id", Uuid, nullable=False),
    Column("dataset_id", Uuid, nullable=False),
    Column("dataset_version_id", Uuid, nullable=False),
    Column("index_profile_id", Uuid, nullable=False),
    Column("ordinal", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("provenance", JSONB, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ForeignKeyConstraint(
        ["document_id", "dataset_version_id", "dataset_id"],
        ["documents.id", "documents.dataset_version_id", "documents.dataset_id"],
    ),
    ForeignKeyConstraint(
        ["dataset_version_id", "dataset_id", "index_profile_id"],
        ["dataset_versions.id", "dataset_versions.dataset_id", "dataset_versions.index_profile_id"],
    ),
    UniqueConstraint("document_id", "ordinal"),
    CheckConstraint("ordinal >= 0", name="nonnegative_ordinal"),
    CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
    CheckConstraint("jsonb_typeof(provenance) = 'object'", name="provenance_object"),
)
ingestion_jobs = Table(
    "ingestion_jobs",
    metadata,
    *identity(),
    *state(),
    Column(
        "dataset_version_id", Uuid, ForeignKey("dataset_versions.id"), nullable=False, index=True
    ),
    Column("processed_documents", Integer, nullable=False, server_default="0"),
    Column("processed_chunks", Integer, nullable=False, server_default="0"),
    Column("total_documents", Integer),
    Column("checkpoint", Text),
    CheckConstraint(
        "processed_documents >= 0 AND processed_chunks >= 0", name="nonnegative_counts"
    ),
    CheckConstraint(
        "total_documents IS NULL OR total_documents >= processed_documents", name="total_documents"
    ),
)
pipeline_configs = Table(
    "pipeline_configs",
    metadata,
    *identity(),
    Column("name", Text, nullable=False),
    Column("index_profile_id", Uuid, ForeignKey("index_profiles.id"), nullable=False),
    Column("strategy", String(32), nullable=False),
    Column("configuration", JSONB, nullable=False),
    CheckConstraint(
        "strategy IN ('DENSE','HYBRID','RERANKED','CRAG',"
        "'SELF_REFLECTIVE_RAG','MULTI_HOP_RAG','AGENTIC_RAG')",
        name="strategy",
    ),
    CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_object"),
)
experiments = Table(
    "experiments",
    metadata,
    *identity(),
    Column("name", Text, nullable=False),
    Column("definition", JSONB, nullable=False),
    Column("question_set_version", Text, nullable=False),
    Column("application_revision", Text, nullable=False),
    CheckConstraint("jsonb_typeof(definition) = 'object'", name="definition_object"),
)
experiment_versions = Table(
    "experiment_versions",
    metadata,
    Column("experiment_id", Uuid, ForeignKey("experiments.id"), primary_key=True),
    Column("dataset_version_id", Uuid, ForeignKey("dataset_versions.id"), primary_key=True),
)
experiment_pipelines = Table(
    "experiment_pipelines",
    metadata,
    Column("experiment_id", Uuid, ForeignKey("experiments.id"), primary_key=True),
    Column("pipeline_config_id", Uuid, ForeignKey("pipeline_configs.id"), primary_key=True),
)
benchmark_questions = Table(
    "benchmark_questions",
    metadata,
    *identity(),
    Column("question_set_version", Text, nullable=False, index=True),
    Column("question", Text, nullable=False),
    Column("reference_answer", Text),
    Column("judgments", JSONB),
)
experiment_runs = Table(
    "experiment_runs",
    metadata,
    *identity(),
    *state(),
    Column("experiment_id", Uuid, ForeignKey("experiments.id"), nullable=False, index=True),
    Column("snapshot", JSONB, nullable=False),
    CheckConstraint("jsonb_typeof(snapshot) = 'object'", name="snapshot_object"),
)
query_runs = Table(
    "query_runs",
    metadata,
    *identity(),
    *state(),
    Column(
        "pipeline_config_id", Uuid, ForeignKey("pipeline_configs.id"), nullable=False, index=True
    ),
    Column("experiment_run_id", Uuid, ForeignKey("experiment_runs.id"), index=True),
    Column("benchmark_question_id", Uuid, ForeignKey("benchmark_questions.id")),
    Column("request", JSONB, nullable=False),
    Column("application_revision", Text, nullable=False),
    Column("result", JSONB),
    CheckConstraint("jsonb_typeof(request) = 'object'", name="request_object"),
)
query_versions = Table(
    "query_versions",
    metadata,
    Column("query_run_id", Uuid, ForeignKey("query_runs.id"), primary_key=True),
    Column("dataset_version_id", Uuid, ForeignKey("dataset_versions.id"), primary_key=True),
)
trace_events = Table(
    "trace_events",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("query_run_id", Uuid, ForeignKey("query_runs.id"), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("stage", String(64), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("ended_at", DateTime(timezone=True)),
    Column("duration_ms", Float),
    Column("data", JSONB, nullable=False, server_default="{}"),
    UniqueConstraint("query_run_id", "sequence"),
    CheckConstraint("sequence >= 0", name="nonnegative_sequence"),
    CheckConstraint(
        "duration_ms IS NULL OR (duration_ms >= 0 AND duration_ms < 'Infinity'::float)",
        name="nonnegative_duration",
    ),
    CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="time_order"),
    CheckConstraint("jsonb_typeof(data) = 'object'", name="data_object"),
)
evaluation_results = Table(
    "evaluation_results",
    metadata,
    *identity(),
    Column("query_run_id", Uuid, ForeignKey("query_runs.id"), nullable=False, index=True),
    Column("benchmark_question_id", Uuid, ForeignKey("benchmark_questions.id")),
    Column("metrics", JSONB, nullable=False),
    CheckConstraint(
        "jsonb_typeof(metrics) = 'array' AND jsonb_array_length(metrics) > 0", name="metrics_array"
    ),
)
