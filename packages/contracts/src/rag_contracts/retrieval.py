from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator, model_validator

from rag_contracts.common import Contract, ModelRef, NonEmpty, NonNegative, unique_scope
from rag_contracts.datasets import Chunk


class PipelineStrategy(StrEnum):
    DENSE = "DENSE"
    HYBRID = "HYBRID"
    RERANKED = "RERANKED"
    CRAG = "CRAG"
    SELF_REFLECTIVE_RAG = "SELF_REFLECTIVE_RAG"
    MULTI_HOP_RAG = "MULTI_HOP_RAG"
    AGENTIC_RAG = "AGENTIC_RAG"


class RetrievalRequest(Contract):
    query: NonEmpty
    dataset_version_ids: tuple[UUID, ...] = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=1000)
    candidate_k: int = Field(default=40, ge=1, le=10_000)
    document_ids: tuple[UUID, ...] = ()

    _unique_versions = field_validator("dataset_version_ids")(unique_scope)
    _unique_documents = field_validator("document_ids")(unique_scope)

    @model_validator(mode="after")
    def check_candidates(self) -> Self:
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be at least top_k")
        return self


class PipelineConfig(Contract):
    id: UUID
    name: NonEmpty
    strategy: PipelineStrategy
    index_profile_id: UUID
    top_k: int = Field(default=10, ge=1, le=1000)
    candidate_k: int = Field(default=40, ge=1, le=10_000)
    reranker: ModelRef | None = None
    generation_model: ModelRef | None = None
    prompt_version: NonEmpty | None = None
    max_steps: int = Field(default=8, ge=1, le=100)
    timeout_seconds: float = Field(default=60, gt=0, le=3600)
    allowed_tools: tuple[NonEmpty, ...] = ()
    created_at: AwareDatetime

    @model_validator(mode="after")
    def check_configuration(self) -> Self:
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be at least top_k")
        if self.generation_model is not None and self.prompt_version is None:
            raise ValueError("generation requires a pinned prompt version")
        return self


class RetrievedChunk(Contract):
    chunk: Chunk
    score: float
    rank: int = Field(ge=1)
    rank_before_rerank: int | None = Field(default=None, ge=1)
    retriever: NonEmpty


class RetrievalResult(Contract):
    request: RetrievalRequest
    index_profile_id: UUID
    retriever: NonEmpty
    hits: tuple[RetrievedChunk, ...]
    stage_durations_ms: dict[str, NonNegative] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_hits(self) -> Self:
        if len(self.hits) > self.request.top_k:
            raise ValueError("hit count exceeds requested top_k")
        if len({hit.chunk.id for hit in self.hits}) != len(self.hits):
            raise ValueError("retrieval hits must be unique")
        for rank, hit in enumerate(self.hits, start=1):
            if hit.rank != rank:
                raise ValueError("hits must be ordered with contiguous ranks")
            if hit.chunk.dataset_version_id not in self.request.dataset_version_ids:
                raise ValueError("hit falls outside requested version scope")
            if hit.chunk.index_profile_id != self.index_profile_id:
                raise ValueError("hit uses an incompatible index profile")
            if self.request.document_ids and hit.chunk.document_id not in self.request.document_ids:
                raise ValueError("hit falls outside requested document scope")
        return self
