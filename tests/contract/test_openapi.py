import json
from pathlib import Path


def test_openapi_is_deterministic_and_has_no_unimplemented_routes():
    from app.main import create_app

    first = create_app().openapi()
    second = create_app().openapi()
    assert first == second
    assert set(first["paths"]) == {"/health", "/ready"}
    expected = {
        "Dataset",
        "DatasetVersion",
        "Document",
        "Chunk",
        "IngestionJob",
        "IndexProfile",
        "PipelineConfig",
        "RetrievalRequest",
        "RetrievedChunk",
        "RetrievalResult",
        "Citation",
        "QueryRun",
        "TraceEvent",
        "ExperimentDefinition",
        "ExperimentRun",
        "BenchmarkQuestion",
        "EvaluationResult",
        "MetricResult",
        "CostUsage",
        "LatencyBreakdown",
        "ErrorResponse",
    }
    schemas = first["components"]["schemas"]
    assert expected <= set(schemas)

    def verify_refs(value):
        if isinstance(value, dict):
            if "$ref" in value:
                assert value["$ref"].startswith("#/components/schemas/")
                assert value["$ref"].rsplit("/", 1)[1] in schemas
            for child in value.values():
                verify_refs(child)
        elif isinstance(value, list):
            for child in value:
                verify_refs(child)

    verify_refs(first)


def test_committed_openapi_matches_application():
    from app.main import create_app

    path = Path(__file__).parents[2] / "packages/contracts/openapi.json"
    assert path.exists(), "run pnpm contracts:generate"
    assert json.loads(path.read_text()) == create_app().openapi()
