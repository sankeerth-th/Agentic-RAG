from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError


def test_retrieval_requires_explicit_unique_version_scope():
    from rag_contracts.retrieval import RetrievalRequest

    version = uuid4()
    request = RetrievalRequest(query="evidence?", dataset_version_ids=(version,), top_k=5)
    assert RetrievalRequest.model_validate_json(request.model_dump_json()) == request
    for changes in (
        {"dataset_version_ids": ()},
        {"dataset_version_ids": (version, version)},
        {"query": "   "},
        {"top_k": 0},
        {"top_k": 1001},
        {"candidate_k": 2},
        {"unexpected": True},
    ):
        with pytest.raises(ValidationError):
            RetrievalRequest.model_validate(request.model_dump() | changes)


def test_unknown_cost_is_distinct_from_zero_and_requires_pricing_provenance():
    from rag_contracts.runs import CostUsage

    assert CostUsage().cost is None
    assert CostUsage().input_tokens is None
    with pytest.raises(ValidationError):
        CostUsage(cost=0)
    known = CostUsage(
        input_tokens=0,
        output_tokens=0,
        cost="0",
        currency="USD",
        pricing_version="test-v1",
        pricing_effective_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert known.cost == 0
    with pytest.raises(ValidationError):
        CostUsage(input_tokens=-1)


def test_chunk_provenance_survives_round_trip():
    from rag_contracts.datasets import Chunk

    data = {
        "id": uuid4(),
        "document_id": uuid4(),
        "dataset_id": uuid4(),
        "dataset_version_id": uuid4(),
        "index_profile_id": uuid4(),
        "ordinal": 0,
        "text": "Source evidence",
        "content_hash": "a" * 64,
        "source": {"kind": "uploaded_object", "uri": "s3://corpus/doc.txt"},
        "source_name": "doc.txt",
        "page": 1,
        "chunking": {"strategy": "fixed", "size": 512, "overlap": 64},
        "ingested_at": datetime.now(UTC),
    }
    chunk = Chunk.model_validate(data)
    assert Chunk.model_validate_json(chunk.model_dump_json()) == chunk
    for field in ("dataset_version_id", "document_id", "index_profile_id", "source"):
        with pytest.raises(ValidationError):
            Chunk.model_validate({k: v for k, v in data.items() if k != field})


def test_chunking_and_pipeline_execution_are_bounded():
    from rag_contracts.datasets import ChunkingConfig
    from rag_contracts.retrieval import PipelineConfig, PipelineStrategy

    with pytest.raises(ValidationError):
        ChunkingConfig(strategy="fixed", size=64, overlap=64)
    pipeline = dict(
        id=uuid4(),
        name="dense",
        strategy="DENSE",
        index_profile_id=uuid4(),
        created_at=datetime.now(UTC),
    )
    for change in ({"max_steps": 0}, {"timeout_seconds": 0}, {"candidate_k": 1}):
        with pytest.raises(ValidationError):
            PipelineConfig.model_validate(pipeline | change)
    assert PipelineStrategy.SELF_REFLECTIVE_RAG.value == "SELF_REFLECTIVE_RAG"


def test_metrics_cannot_silently_turn_unavailable_values_into_scores():
    from rag_contracts.experiments import MetricResult

    base = dict(name="recall_at_k", version="1", status="unavailable", reason="no judgments")
    assert MetricResult(**base).value is None
    with pytest.raises(ValidationError):
        MetricResult(name="recall_at_k", version="1", status="completed")
    with pytest.raises(ValidationError):
        MetricResult(name="recall_at_k", version="1", status="completed", value=float("nan"))
    with pytest.raises(ValidationError):
        MetricResult(**base, value=0)


def test_snapshots_reject_reassignment_and_naive_timestamps():
    from rag_contracts.datasets import IndexProfile

    data = dict(
        id=uuid4(),
        name="local-dense",
        dimension=768,
        distance="cosine",
        dense_model={"provider": "local", "name": "test-embed", "revision": "v1"},
        created_at=datetime.now(UTC),
    )
    profile = IndexProfile.model_validate(data)
    with pytest.raises(ValidationError):
        profile.dimension = 1024
    with pytest.raises(ValidationError):
        IndexProfile.model_validate(data | {"created_at": datetime(2026, 1, 1)})
