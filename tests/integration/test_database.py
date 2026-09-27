from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, ProgrammingError


@pytest.fixture
def engine():
    from app.core.config import Settings
    from app.core.database import create_database_engine

    engine = create_database_engine(Settings())
    yield engine
    engine.dispose()


def test_migration_contains_foundation_entities(engine):
    expected = {
        "datasets",
        "dataset_versions",
        "index_profiles",
        "documents",
        "chunks",
        "ingestion_jobs",
        "pipeline_configs",
        "query_runs",
        "trace_events",
        "experiments",
        "experiment_runs",
        "evaluation_results",
        "benchmark_questions",
    }
    assert expected <= set(inspect(engine).get_table_names())


def test_database_rejects_mutating_published_version_and_cross_dataset_document(engine):
    from app.core.models import dataset_versions, datasets, documents, index_profiles

    with engine.connect() as connection:
        transaction = connection.begin()
        dataset, other, profile, version = (uuid4() for _ in range(4))
        connection.execute(
            datasets.insert(), [{"id": dataset, "name": "a"}, {"id": other, "name": "b"}]
        )
        connection.execute(
            index_profiles.insert(), {"id": profile, "name": "test", "configuration": {}}
        )
        data = dict(
            id=version,
            dataset_id=dataset,
            index_profile_id=profile,
            version=1,
            content_hash="a" * 64,
            configuration={},
            document_manifest_uri="s3://test/manifest",
        )
        connection.execute(dataset_versions.insert(), data)
        with pytest.raises(ProgrammingError, match="immutable"), connection.begin_nested():
            connection.execute(
                dataset_versions.update().where(dataset_versions.c.id == version).values(version=2)
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                documents.insert(),
                dict(
                    id=uuid4(),
                    dataset_id=other,
                    dataset_version_id=version,
                    source={},
                    title="wrong scope",
                    object_key="doc.txt",
                    content_hash="b" * 64,
                    byte_size=1,
                ),
            )
        transaction.rollback()


def test_duplicate_dataset_version_and_trace_sequence_are_rejected(engine):
    from app.core.models import (
        dataset_versions,
        datasets,
        index_profiles,
        pipeline_configs,
        query_runs,
        trace_events,
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        dataset, profile, version, pipeline, run = (uuid4() for _ in range(5))
        connection.execute(datasets.insert(), {"id": dataset, "name": "test"})
        connection.execute(
            index_profiles.insert(), {"id": profile, "name": "test", "configuration": {}}
        )
        values = dict(
            id=version,
            dataset_id=dataset,
            index_profile_id=profile,
            version=1,
            content_hash="c" * 64,
            configuration={},
            document_manifest_uri="s3://test/manifest",
        )
        connection.execute(dataset_versions.insert(), values)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                dataset_versions.insert(), values | {"id": uuid4(), "content_hash": "d" * 64}
            )
        connection.execute(
            pipeline_configs.insert(),
            dict(
                id=pipeline,
                name="dense",
                strategy="DENSE",
                index_profile_id=profile,
                configuration={},
            ),
        )
        connection.execute(
            query_runs.insert(),
            dict(
                id=run,
                pipeline_config_id=pipeline,
                status="queued",
                request={},
                application_revision="test",
            ),
        )
        event = dict(id=uuid4(), query_run_id=run, sequence=0, stage="query_received")
        connection.execute(trace_events.insert(), event)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(trace_events.insert(), event | {"id": uuid4()})
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        transaction.rollback()


def test_configuration_change_can_version_the_same_content(engine):
    from app.core.models import dataset_versions, datasets, index_profiles

    with engine.connect() as connection:
        transaction = connection.begin()
        dataset, profile = uuid4(), uuid4()
        connection.execute(datasets.insert(), {"id": dataset, "name": "test"})
        connection.execute(
            index_profiles.insert(), {"id": profile, "name": "test", "configuration": {}}
        )
        for number, size in ((1, 256), (2, 512)):
            connection.execute(
                dataset_versions.insert(),
                dict(
                    id=uuid4(),
                    dataset_id=dataset,
                    index_profile_id=profile,
                    version=number,
                    content_hash="e" * 64,
                    configuration={"chunk_size": size},
                    document_manifest_uri="s3://test/manifest",
                ),
            )
        transaction.rollback()


def test_membership_cannot_expand_pinned_query_or_experiment_scope(engine):
    from app.core.models import (
        dataset_versions,
        datasets,
        experiment_pipelines,
        experiment_versions,
        experiments,
        index_profiles,
        pipeline_configs,
        query_runs,
        query_versions,
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        dataset, profile, first, second, pipeline, other_pipeline, run, experiment = (
            uuid4() for _ in range(8)
        )
        connection.execute(datasets.insert(), {"id": dataset, "name": "test"})
        connection.execute(
            index_profiles.insert(), {"id": profile, "name": "test", "configuration": {}}
        )
        for number, version in enumerate((first, second), start=1):
            connection.execute(
                dataset_versions.insert(),
                dict(
                    id=version,
                    dataset_id=dataset,
                    index_profile_id=profile,
                    version=number,
                    content_hash=str(number) * 64,
                    configuration={},
                    document_manifest_uri="s3://test/manifest",
                ),
            )
        for identifier in (pipeline, other_pipeline):
            connection.execute(
                pipeline_configs.insert(),
                dict(
                    id=identifier,
                    name="dense",
                    strategy="DENSE",
                    index_profile_id=profile,
                    configuration={},
                ),
            )
        connection.execute(
            query_runs.insert(),
            dict(
                id=run,
                pipeline_config_id=pipeline,
                status="completed",
                request={"dataset_version_ids": [str(first)]},
                application_revision="test",
            ),
        )
        connection.execute(
            experiments.insert(),
            dict(
                id=experiment,
                name="test",
                question_set_version="test-v1",
                application_revision="test",
                definition={
                    "dataset_version_ids": [str(first)],
                    "pipeline_config_ids": [str(pipeline)],
                },
            ),
        )
        for table, valid, invalid in (
            (
                query_versions,
                {"query_run_id": run, "dataset_version_id": first},
                {"dataset_version_id": second},
            ),
            (
                experiment_versions,
                {"experiment_id": experiment, "dataset_version_id": first},
                {"dataset_version_id": second},
            ),
            (
                experiment_pipelines,
                {"experiment_id": experiment, "pipeline_config_id": pipeline},
                {"pipeline_config_id": other_pipeline},
            ),
        ):
            connection.execute(table.insert(), valid)
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(table.insert(), valid | invalid)
        transaction.rollback()
