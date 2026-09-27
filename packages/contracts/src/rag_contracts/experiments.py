from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator, model_validator

from rag_contracts.common import ConfigMap, Contract, ModelRef, NonEmpty, RunStatus, unique_scope


class BenchmarkQuestion(Contract):
    id: UUID
    question_set_version: NonEmpty
    question: NonEmpty
    reference_answer: str | None = None
    relevant_document_ids: tuple[UUID, ...] | None = None
    relevant_chunk_ids: tuple[UUID, ...] | None = None


class MetricConfig(Contract):
    name: NonEmpty
    version: NonEmpty
    parameters: ConfigMap = Field(default_factory=dict)
    evaluator_model: ModelRef | None = None


class MetricResult(MetricConfig):
    status: Literal["completed", "unavailable", "failed"]
    value: float | None = None
    reason: NonEmpty | None = None

    @model_validator(mode="after")
    def check_value(self) -> Self:
        if self.status == "completed" and self.value is None:
            raise ValueError("completed metric requires a value")
        if self.status != "completed" and (self.value is not None or self.reason is None):
            raise ValueError("unavailable or failed metric needs a reason and no value")
        return self


class ExperimentDefinition(Contract):
    id: UUID
    name: NonEmpty
    dataset_version_ids: tuple[UUID, ...] = Field(min_length=1)
    pipeline_config_ids: tuple[UUID, ...] = Field(min_length=1)
    question_set_version: NonEmpty
    question_set_uri: NonEmpty
    metrics: tuple[MetricConfig, ...] = Field(min_length=1)
    application_revision: NonEmpty
    created_at: AwareDatetime

    _unique_versions = field_validator("dataset_version_ids")(unique_scope)
    _unique_pipelines = field_validator("pipeline_config_ids")(unique_scope)


class ExperimentRun(Contract):
    id: UUID
    definition: ExperimentDefinition
    status: RunStatus
    created_at: AwareDatetime
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None


class EvaluationResult(Contract):
    id: UUID
    query_run_id: UUID
    benchmark_question_id: UUID | None = None
    metrics: tuple[MetricResult, ...] = Field(min_length=1)
    created_at: AwareDatetime
