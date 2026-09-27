from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from rag_contracts.common import ModelRef
from rag_contracts.retrieval import RetrievalRequest, RetrievalResult
from rag_contracts.runs import Citation, QueryRun


def test_nested_configuration_is_read_only_and_round_trips():
    model = ModelRef(
        provider="local",
        name="test",
        revision="1",
        parameters={
            "nested": {"weights": [1, 2]},
        },
    )
    with pytest.raises(TypeError):
        model.parameters["temperature"] = 100
    with pytest.raises(TypeError):
        model.parameters["nested"]["weights"][0] = 99
    assert ModelRef.model_validate_json(model.model_dump_json()) == model
    empty = ModelRef(provider="local", name="test", revision="1")
    with pytest.raises(TypeError):
        empty.parameters["temperature"] = 100


def test_query_run_rejects_evidence_outside_its_pinned_scope():
    requested, other = uuid4(), uuid4()
    request = RetrievalRequest(query="original", dataset_version_ids=(requested,))
    run = dict(
        id=uuid4(),
        pipeline_config_id=uuid4(),
        request=request,
        status="completed",
        application_revision="test",
        created_at=datetime.now(UTC),
    )
    wrong = RetrievalResult(
        request=RetrievalRequest(query="rewritten", dataset_version_ids=(other,)),
        index_profile_id=uuid4(),
        retriever="dense",
        hits=(),
    )
    with pytest.raises(ValidationError):
        QueryRun(**run, retrieval=wrong)
    allowed_rewrite = wrong.model_copy(
        update={"request": request.model_copy(update={"query": "rewritten"})}
    )
    assert QueryRun(**run, retrieval=allowed_rewrite).retrieval.request.query == "rewritten"
    citation = Citation(
        id="c1",
        claim="claim",
        chunk_id=uuid4(),
        document_id=uuid4(),
        dataset_id=uuid4(),
        dataset_version_id=other,
    )
    with pytest.raises(ValidationError):
        QueryRun(**run, citations=(citation,))
