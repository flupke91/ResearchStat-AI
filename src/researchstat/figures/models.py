"""Data models for the professional figure engine."""

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from ..engine.models import AnalysisResult


class FigureKind(str, Enum):
    SCATTER = "scatter"
    BOXPLOT = "boxplot"
    VIOLIN = "violin"
    SURVIVAL = "survival"


@dataclass(frozen=True)
class FigureRequest:
    kind: FigureKind
    data: pd.DataFrame
    x: str | None = None
    y: str | None = None
    group: str | None = None
    time: str | None = None
    survival: str | None = None
    analysis_result: AnalysisResult | None = None
    analysis_id: str | None = None
    width: float = 6.4
    height: float = 4.8
    dpi: int = 300
