"""foundation schema"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benchmark_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("question_set_version", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("judgments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_questions")),
    )
    op.create_index(
        op.f("ix_benchmark_questions_question_set_version"),
        "benchmark_questions",
        ["question_set_version"],
        unique=False,
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("length(btrim(name)) > 0", name=op.f("ck_datasets_name_not_empty")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datasets")),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("question_set_version", sa.Text(), nullable=False),
        sa.Column("application_revision", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(definition) = 'object'", name=op.f("ck_experiments_definition_object")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiments")),
    )
    op.create_table(
        "index_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'",
            name=op.f("ck_index_profiles_configuration_object"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_index_profiles")),
    )
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("index_profile_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("document_manifest_uri", sa.Text(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'", name=op.f("ck_dataset_versions_content_hash")
        ),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'",
            name=op.f("ck_dataset_versions_configuration_object"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_dataset_versions_positive_version")),
        sa.ForeignKeyConstraint(
            ["dataset_id"], ["datasets.id"], name=op.f("fk_dataset_versions_dataset_id_datasets")
        ),
        sa.ForeignKeyConstraint(
            ["index_profile_id"],
            ["index_profiles.id"],
            name=op.f("fk_dataset_versions_index_profile_id_index_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_versions")),
        sa.UniqueConstraint("dataset_id", "version", name=op.f("uq_dataset_versions_dataset_id")),
        sa.UniqueConstraint(
            "id", "dataset_id", "index_profile_id", name="uq_dataset_versions_profile"
        ),
        sa.UniqueConstraint("id", "dataset_id", name="uq_dataset_versions_dataset"),
    )
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(snapshot) = 'object'", name=op.f("ck_experiment_runs_snapshot_object")
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','failed','cancelled')",
            name=op.f("ck_experiment_runs_valid_status"),
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name=op.f("ck_experiment_runs_time_order"),
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["experiments.id"],
            name=op.f("fk_experiment_runs_experiment_id_experiments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiment_runs")),
    )
    op.create_index(
        op.f("ix_experiment_runs_experiment_id"), "experiment_runs", ["experiment_id"], unique=False
    )
    op.create_table(
        "pipeline_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("index_profile_id", sa.Uuid(), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'",
            name=op.f("ck_pipeline_configs_configuration_object"),
        ),
        sa.CheckConstraint(
            "strategy IN ('DENSE','HYBRID','RERANKED','CRAG',"
            "'SELF_REFLECTIVE_RAG','MULTI_HOP_RAG','AGENTIC_RAG')",
            name=op.f("ck_pipeline_configs_strategy"),
        ),
        sa.ForeignKeyConstraint(
            ["index_profile_id"],
            ["index_profiles.id"],
            name=op.f("fk_pipeline_configs_index_profile_id_index_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_configs")),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'", name=op.f("ck_documents_content_hash")
        ),
        sa.CheckConstraint(
            "jsonb_typeof(source) = 'object'", name=op.f("ck_documents_source_object")
        ),
        sa.CheckConstraint("byte_size >= 0", name=op.f("ck_documents_nonnegative_size")),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "dataset_id"],
            ["dataset_versions.id", "dataset_versions.dataset_id"],
            name=op.f("fk_documents_dataset_version_id_dataset_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("dataset_version_id", "object_key", name="uq_documents_version_object"),
        sa.UniqueConstraint(
            "id", "dataset_version_id", "dataset_id", name="uq_documents_provenance"
        ),
    )
    op.create_table(
        "experiment_pipelines",
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_config_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["experiments.id"],
            name=op.f("fk_experiment_pipelines_experiment_id_experiments"),
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_config_id"],
            ["pipeline_configs.id"],
            name=op.f("fk_experiment_pipelines_pipeline_config_id_pipeline_configs"),
        ),
        sa.PrimaryKeyConstraint(
            "experiment_id", "pipeline_config_id", name=op.f("pk_experiment_pipelines")
        ),
    )
    op.create_table(
        "experiment_versions",
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name=op.f("fk_experiment_versions_dataset_version_id_dataset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["experiments.id"],
            name=op.f("fk_experiment_versions_experiment_id_experiments"),
        ),
        sa.PrimaryKeyConstraint(
            "experiment_id", "dataset_version_id", name=op.f("pk_experiment_versions")
        ),
    )
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("processed_documents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_chunks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_documents", sa.Integer(), nullable=True),
        sa.Column("checkpoint", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','failed','cancelled')",
            name=op.f("ck_ingestion_jobs_valid_status"),
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name=op.f("ck_ingestion_jobs_time_order"),
        ),
        sa.CheckConstraint(
            "processed_documents >= 0 AND processed_chunks >= 0",
            name=op.f("ck_ingestion_jobs_nonnegative_counts"),
        ),
        sa.CheckConstraint(
            "total_documents IS NULL OR total_documents >= processed_documents",
            name=op.f("ck_ingestion_jobs_total_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name=op.f("fk_ingestion_jobs_dataset_version_id_dataset_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_jobs")),
    )
    op.create_index(
        op.f("ix_ingestion_jobs_dataset_version_id"),
        "ingestion_jobs",
        ["dataset_version_id"],
        unique=False,
    )
    op.create_table(
        "query_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pipeline_config_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_run_id", sa.Uuid(), nullable=True),
        sa.Column("benchmark_question_id", sa.Uuid(), nullable=True),
        sa.Column("request", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("application_revision", sa.Text(), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "jsonb_typeof(request) = 'object'", name=op.f("ck_query_runs_request_object")
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','failed','cancelled')",
            name=op.f("ck_query_runs_valid_status"),
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name=op.f("ck_query_runs_time_order"),
        ),
        sa.ForeignKeyConstraint(
            ["benchmark_question_id"],
            ["benchmark_questions.id"],
            name=op.f("fk_query_runs_benchmark_question_id_benchmark_questions"),
        ),
        sa.ForeignKeyConstraint(
            ["experiment_run_id"],
            ["experiment_runs.id"],
            name=op.f("fk_query_runs_experiment_run_id_experiment_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_config_id"],
            ["pipeline_configs.id"],
            name=op.f("fk_query_runs_pipeline_config_id_pipeline_configs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_query_runs")),
    )
    op.create_index(
        op.f("ix_query_runs_experiment_run_id"), "query_runs", ["experiment_run_id"], unique=False
    )
    op.create_index(
        op.f("ix_query_runs_pipeline_config_id"), "query_runs", ["pipeline_config_id"], unique=False
    )
    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("index_profile_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name=op.f("ck_chunks_content_hash")),
        sa.CheckConstraint(
            "jsonb_typeof(provenance) = 'object'", name=op.f("ck_chunks_provenance_object")
        ),
        sa.CheckConstraint("ordinal >= 0", name=op.f("ck_chunks_nonnegative_ordinal")),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "dataset_id", "index_profile_id"],
            [
                "dataset_versions.id",
                "dataset_versions.dataset_id",
                "dataset_versions.index_profile_id",
            ],
            name=op.f("fk_chunks_dataset_version_id_dataset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "dataset_version_id", "dataset_id"],
            ["documents.id", "documents.dataset_version_id", "documents.dataset_id"],
            name=op.f("fk_chunks_document_id_documents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunks")),
        sa.UniqueConstraint("document_id", "ordinal", name=op.f("uq_chunks_document_id")),
    )
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("query_run_id", sa.Uuid(), nullable=False),
        sa.Column("benchmark_question_id", sa.Uuid(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(metrics) = 'array' AND jsonb_array_length(metrics) > 0",
            name=op.f("ck_evaluation_results_metrics_array"),
        ),
        sa.ForeignKeyConstraint(
            ["benchmark_question_id"],
            ["benchmark_questions.id"],
            name=op.f("fk_evaluation_results_benchmark_question_id_benchmark_questions"),
        ),
        sa.ForeignKeyConstraint(
            ["query_run_id"],
            ["query_runs.id"],
            name=op.f("fk_evaluation_results_query_run_id_query_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_results")),
    )
    op.create_index(
        op.f("ix_evaluation_results_query_run_id"),
        "evaluation_results",
        ["query_run_id"],
        unique=False,
    )
    op.create_table(
        "query_versions",
        sa.Column("query_run_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name=op.f("fk_query_versions_dataset_version_id_dataset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["query_run_id"],
            ["query_runs.id"],
            name=op.f("fk_query_versions_query_run_id_query_runs"),
        ),
        sa.PrimaryKeyConstraint(
            "query_run_id", "dataset_version_id", name=op.f("pk_query_versions")
        ),
    )
    op.create_table(
        "trace_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("query_run_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column(
            "data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.CheckConstraint(
            "duration_ms IS NULL OR (duration_ms >= 0 AND duration_ms < 'Infinity'::float)",
            name=op.f("ck_trace_events_nonnegative_duration"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(data) = 'object'", name=op.f("ck_trace_events_data_object")
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at", name=op.f("ck_trace_events_time_order")
        ),
        sa.CheckConstraint("sequence >= 0", name=op.f("ck_trace_events_nonnegative_sequence")),
        sa.ForeignKeyConstraint(
            ["query_run_id"],
            ["query_runs.id"],
            name=op.f("fk_trace_events_query_run_id_query_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trace_events")),
        sa.UniqueConstraint("query_run_id", "sequence", name=op.f("uq_trace_events_query_run_id")),
    )
    op.execute("""
        CREATE FUNCTION reject_snapshot_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'published snapshot is immutable';
        END;
        $$
    """)
    for table in (
        "index_profiles",
        "dataset_versions",
        "documents",
        "chunks",
        "pipeline_configs",
        "experiments",
        "experiment_versions",
        "experiment_pipelines",
        "benchmark_questions",
        "query_versions",
        "trace_events",
        "evaluation_results",
    ):
        op.execute(
            f"CREATE TRIGGER immutable_snapshot BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_snapshot_mutation()"
        )
    op.execute("""
        CREATE FUNCTION protect_run_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE field_name text;
        BEGIN
            FOREACH field_name IN ARRAY TG_ARGV LOOP
                IF to_jsonb(NEW)->field_name IS DISTINCT FROM to_jsonb(OLD)->field_name THEN
                    RAISE EXCEPTION 'run configuration is immutable';
                END IF;
            END LOOP;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER immutable_run_configuration BEFORE UPDATE ON query_runs
        FOR EACH ROW EXECUTE FUNCTION protect_run_snapshot(
            'id', 'created_at', 'pipeline_config_id', 'experiment_run_id',
            'benchmark_question_id', 'request', 'application_revision'
        )
    """)
    op.execute("""
        CREATE TRIGGER immutable_run_configuration BEFORE UPDATE ON experiment_runs
        FOR EACH ROW EXECUTE FUNCTION protect_run_snapshot(
            'id', 'created_at', 'experiment_id', 'snapshot'
        )
    """)
    op.execute("""
        CREATE FUNCTION validate_snapshot_membership() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE scope jsonb; member uuid;
        BEGIN
            IF TG_TABLE_NAME = 'query_versions' THEN
                SELECT request->'dataset_version_ids' INTO scope
                    FROM query_runs WHERE id = NEW.query_run_id;
                member := NEW.dataset_version_id;
            ELSIF TG_TABLE_NAME = 'experiment_versions' THEN
                SELECT definition->'dataset_version_ids' INTO scope
                    FROM experiments WHERE id = NEW.experiment_id;
                member := NEW.dataset_version_id;
            ELSE
                SELECT definition->'pipeline_config_ids' INTO scope
                    FROM experiments WHERE id = NEW.experiment_id;
                member := NEW.pipeline_config_id;
            END IF;
            IF scope IS NULL OR NOT (scope @> jsonb_build_array(member::text)) THEN
                RAISE EXCEPTION 'membership outside pinned scope' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    for table in ("query_versions", "experiment_versions", "experiment_pipelines"):
        op.execute(
            f"CREATE TRIGGER pinned_membership BEFORE INSERT ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION validate_snapshot_membership()"
        )


def downgrade() -> None:
    op.drop_table("trace_events")
    op.drop_table("query_versions")
    op.drop_index(op.f("ix_evaluation_results_query_run_id"), table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_table("chunks")
    op.drop_index(op.f("ix_query_runs_pipeline_config_id"), table_name="query_runs")
    op.drop_index(op.f("ix_query_runs_experiment_run_id"), table_name="query_runs")
    op.drop_table("query_runs")
    op.drop_index(op.f("ix_ingestion_jobs_dataset_version_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_table("experiment_versions")
    op.drop_table("experiment_pipelines")
    op.drop_table("documents")
    op.drop_table("pipeline_configs")
    op.drop_index(op.f("ix_experiment_runs_experiment_id"), table_name="experiment_runs")
    op.drop_table("experiment_runs")
    op.drop_table("dataset_versions")
    op.drop_table("index_profiles")
    op.drop_table("experiments")
    op.drop_table("datasets")
    op.drop_index(
        op.f("ix_benchmark_questions_question_set_version"), table_name="benchmark_questions"
    )
    op.drop_table("benchmark_questions")
    op.execute("DROP FUNCTION protect_run_snapshot()")
    op.execute("DROP FUNCTION reject_snapshot_mutation()")
    op.execute("DROP FUNCTION validate_snapshot_membership()")
