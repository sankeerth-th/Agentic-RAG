from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from rag_contracts.common import (
    ConfigMap,
    Contract,
    ErrorInfo,
    ModelRef,
    NonEmpty,
    NonNegative,
    RunStatus,
)
from rag_contracts.retrieval import RetrievalRequest, RetrievalResult


class CostUsage(Contract):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cached_tokens: int | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    pricing_version: NonEmpty | None = None
    pricing_effective_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_price_source(self) -> Self:
        if self.cost is not None and any(
            x is None for x in (self.currency, self.pricing_version, self.pricing_effective_at)
        ):
            raise ValueError("known cost requires currency and pricing provenance")
        return self


class LatencyBreakdown(Contract):
    total_ms: NonNegative
    stages_ms: dict[str, NonNegative] = Field(default_factory=dict)


class Citation(Contract):
    id: NonEmpty
    claim: NonEmpty
    chunk_id: UUID
    document_id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    quote: str | None = None


class QueryRun(Contract):
    id: UUID
    pipeline_config_id: UUID
    request: RetrievalRequest
    status: RunStatus
    application_revision: NonEmpty
    generation_model: ModelRef | None = None
    retrieval: RetrievalResult | None = None
    answer: str | None = None
    citations: tuple[Citation, ...] = ()
    usage: CostUsage = Field(default_factory=CostUsage)
    latency: LatencyBreakdown | None = None
    error: ErrorInfo | None = None
    created_at: AwareDatetime
    finished_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_evidence_scope(self) -> Self:
        evidence = {}
        if self.retrieval is not None:
            if not set(self.retrieval.request.dataset_version_ids) <= set(
                self.request.dataset_version_ids
            ):
                raise ValueError("retrieval falls outside the run's version scope")
            evidence = {hit.chunk.id: hit.chunk for hit in self.retrieval.hits}
            if self.request.document_ids and any(
                chunk.document_id not in self.request.document_ids for chunk in evidence.values()
            ):
                raise ValueError("retrieval falls outside the run's document scope")
        if len({citation.id for citation in self.citations}) != len(self.citations):
            raise ValueError("citation IDs must be unique")
        for citation in self.citations:
            chunk = evidence.get(citation.chunk_id)
            if chunk is None or any(
                getattr(citation, field) != getattr(chunk, field)
                for field in ("document_id", "dataset_id", "dataset_version_id")
            ):
                raise ValueError(
                    "citation must reference retrieved evidence with matching provenance"
                )
        return self


class TraceEvent(Contract):
    id: UUID
    query_run_id: UUID
    sequence: int = Field(ge=0)
    stage: Literal[
        "query_received",
        "query_rewrite",
        "dataset_selection",
        "dense_retrieval",
        "sparse_retrieval",
        "fusion",
        "rerank",
        "retrieval_grade",
        "agent_decision",
        "tool_call",
        "generation",
        "citation_validation",
        "evaluation",
        "run_complete",
        "run_failed",
    ]
    started_at: AwareDatetime
    ended_at: AwareDatetime | None = None
    duration_ms: NonNegative | None = None
    configuration: ConfigMap = Field(default_factory=dict)
    input_refs: tuple[NonEmpty, ...] = ()
    output_refs: tuple[NonEmpty, ...] = ()
    metrics: dict[str, float] = Field(default_factory=dict)
    error: ErrorInfo | None = None

    @model_validator(mode="after")
    def check_time_order(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("end time cannot precede start time")
        return self
