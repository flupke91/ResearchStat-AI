"""Models for statistical plans."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class VariableType(str, Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    UNKNOWN = "unknown"


class GroupStructure(str, Enum):
    INDEPENDENT = "independent"
    PAIRED = "paired"
    REPEATED_MEASURES = "repeated_measures"
    NESTED = "nested"
    WIDE_FORMAT = "wide_format"
    UNKNOWN = "unknown"


class StatisticalPlan(BaseModel):
    status: Literal["ready", "needs_more_info"]
    experiment_type: str = "unknown"
    variable_type: VariableType = VariableType.UNKNOWN
    groups: int | None = None
    group_structure: GroupStructure = GroupStructure.UNKNOWN
    recommended_protocol_id: str | None = None
    reason: str = ""
    assumptions_to_check: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
