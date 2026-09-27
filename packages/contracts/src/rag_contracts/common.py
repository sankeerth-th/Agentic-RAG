from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, PlainSerializer

NonEmpty = Annotated[str, Field(min_length=1)]
ContentHash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonNegative = Annotated[float, Field(ge=0)]


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(child) for child in value)
    return value


def _serialize_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _serialize_json(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_serialize_json(child) for child in value]
    return value


ConfigMap = Annotated[
    Mapping[str, JsonValue],
    AfterValidator(_freeze_json),
    PlainSerializer(_serialize_json, return_type=dict[str, JsonValue]),
]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
        validate_default=True,
    )


class ModelRef(Contract):
    provider: NonEmpty
    name: NonEmpty
    revision: NonEmpty
    parameters: ConfigMap = Field(default_factory=dict)


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorInfo(Contract):
    code: NonEmpty
    message: NonEmpty


class ErrorResponse(Contract):
    error: ErrorInfo
    request_id: NonEmpty


def unique_scope(values: tuple) -> tuple:
    if len(values) != len(set(values)):
        raise ValueError("scope must not contain duplicate IDs")
    return values
