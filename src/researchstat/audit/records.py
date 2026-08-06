"""Audit record creation and persistence."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from .. import __version__
from ..engine.models import AnalysisRequest, AnalysisResult, EngineInfo
from ..planner.models import StatisticalPlan
from ..review.models import PlanReview


class AnalysisRecord(BaseModel):
    analysis_id: str
    timestamp: datetime
    user_input: str
    dataset_hash: str
    protocol_id: str
    software_version: str
    library_version: dict[str, str] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    engine: EngineInfo | None = None
    plan: StatisticalPlan | None = None
    human_review: PlanReview | None = None


class DuplicateAnalysisRecordError(FileExistsError):
    """Raised when an analysis id is written twice."""


class AuditWriter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, record: AnalysisRecord) -> Path:
        path = self.output_dir / f"{record.analysis_id}.json"
        if path.exists():
            raise DuplicateAnalysisRecordError(
                f"Analysis record already exists: {path}"
            )
        path.write_text(
            record.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        return path

    def list_records(self) -> list[Path]:
        return sorted(self.output_dir.glob("*.json"))


def canonical_dataset_hash(data: pd.DataFrame) -> str:
    frame = data.copy()
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].astype(str)
    csv_bytes = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()


def create_analysis_record(
    request: AnalysisRequest,
    result: AnalysisResult,
    user_input: str,
    analysis_id: str | None = None,
    plan: StatisticalPlan | None = None,
    human_review: PlanReview | None = None,
) -> AnalysisRecord:
    record = AnalysisRecord(
        analysis_id=analysis_id or uuid.uuid4().hex,
        timestamp=datetime.now(timezone.utc),
        user_input=user_input,
        dataset_hash=canonical_dataset_hash(request.data),
        protocol_id=result.protocol_id,
        software_version=__version__,
        library_version=result.engine.libraries,
        parameters=result.parameters,
        results=result.model_dump(),
        warnings=result.warnings,
        engine=result.engine,
        plan=plan,
        human_review=human_review,
    )
    return record
