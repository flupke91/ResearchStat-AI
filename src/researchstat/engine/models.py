"""Standard input and output models for statistical analyses."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class EngineInfo(BaseModel):
    name: str
    version: str
    libraries: dict[str, str] = Field(default_factory=dict)


class AssumptionCheck(BaseModel):
    name: str
    passed: bool | None = None
    statistic: float | None = None
    p_value: float | None = None
    detail: str = ""


class AnalysisResult(BaseModel):
    protocol_id: str
    method: str
    engine: EngineInfo
    statistics: dict[str, Any] = Field(default_factory=dict)
    p_values: dict[str, Any] = Field(default_factory=dict)
    effect_size: dict[str, float] = Field(default_factory=dict)
    assumptions: list[AssumptionCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisRequest:
    protocol_id: str
    data: pd.DataFrame
    outcome: str
    group: str | None = None
    factor2: str | None = None
    paired_by: str | None = None
    predictors: tuple[str, ...] = ()
    alpha: float | None = None
