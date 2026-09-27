from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from rag_contracts.common import (
    ConfigMap,
    ContentHash,
    Contract,
    ErrorInfo,
    ModelRef,
    NonEmpty,
    RunStatus,
)


class SourceConfig(Contract):
    kind: Literal["local_file", "uploaded_object", "huggingface", "url", "git"]
    uri: NonEmpty
    revision: str | None = None


class ParserConfig(Contract):
    name: NonEmpty
    revision: NonEmpty
    options: ConfigMap = Field(default_factory=dict)


class ChunkingConfig(Contract):
    strategy: Literal["fixed", "recursive", "heading"]
    size: int = Field(gt=0, le=1_000_000)
    overlap: int = Field(default=0, ge=0)
    unit: Literal["tokens", "characters"] = "tokens"
    revision: NonEmpty = "1"

    @model_validator(mode="after")
    def check_overlap(self) -> Self:
        if self.overlap >= self.size:
            raise ValueError("overlap must be smaller than chunk size")
        return self


class Dataset(Contract):
    id: UUID
    name: NonEmpty
    description: str | None = None
    created_at: AwareDatetime


class IndexProfile(Contract):
    id: UUID
    name: NonEmpty
    dense_model: ModelRef
    dimension: int = Field(gt=0, le=65_536)
    distance: Literal["cosine", "dot", "euclid", "manhattan"]
    sparse_model: ModelRef | None = None
    created_at: AwareDatetime


class DatasetVersion(Contract):
    id: UUID
    dataset_id: UUID
    version: int = Field(ge=1)
    source: SourceConfig
    parser: ParserConfig
    chunking: ChunkingConfig
    index_profile_id: UUID
    document_manifest_uri: NonEmpty
    content_hash: ContentHash
    created_at: AwareDatetime


class Document(Contract):
    id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    source: SourceConfig
    title: NonEmpty
    object_key: NonEmpty
    content_hash: ContentHash
    byte_size: int = Field(ge=0)
    created_at: AwareDatetime


class Chunk(Contract):
    id: UUID
    document_id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    source: SourceConfig
    source_name: NonEmpty
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    ordinal: int = Field(ge=0)
    text: NonEmpty
    content_hash: ContentHash
    ingested_at: AwareDatetime
    chunking: ChunkingConfig
    index_profile_id: UUID


class IngestionJob(Contract):
    id: UUID
    dataset_version_id: UUID
    status: RunStatus
    processed_documents: int = Field(default=0, ge=0)
    processed_chunks: int = Field(default=0, ge=0)
    total_documents: int | None = Field(default=None, ge=0)
    checkpoint: str | None = None
    error: ErrorInfo | None = None
    created_at: AwareDatetime
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
