from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic.json_schema import models_json_schema
from rag_contracts.datasets import (
    Chunk,
    Dataset,
    DatasetVersion,
    Document,
    IndexProfile,
    IngestionJob,
)
from rag_contracts.experiments import (
    BenchmarkQuestion,
    EvaluationResult,
    ExperimentDefinition,
    ExperimentRun,
    MetricResult,
)
from rag_contracts.retrieval import (
    PipelineConfig,
    RetrievalRequest,
    RetrievalResult,
    RetrievedChunk,
)
from rag_contracts.runs import Citation, CostUsage, LatencyBreakdown, QueryRun, TraceEvent


def build_openapi(app: FastAPI) -> dict[str, Any]:
    models = (
        Dataset,
        DatasetVersion,
        Document,
        Chunk,
        IngestionJob,
        IndexProfile,
        PipelineConfig,
        RetrievalRequest,
        RetrievedChunk,
        RetrievalResult,
        Citation,
        QueryRun,
        TraceEvent,
        ExperimentDefinition,
        ExperimentRun,
        BenchmarkQuestion,
        EvaluationResult,
        MetricResult,
        CostUsage,
        LatencyBreakdown,
    )
    _, domain = models_json_schema(
        [(model, "validation") for model in models],
        ref_template="#/components/schemas/{model}",
    )
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {}).setdefault("schemas", {}).update(domain["$defs"])
    return schema
