"""Plan -> review -> execute -> audit workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..audit.records import AuditWriter, create_analysis_record
from ..engine.models import AnalysisRequest
from ..engine.python_engine import run_analysis
from ..planner.models import StatisticalPlan
from ..planner.planner import StatisticalPlanner
from ..privacy.masking import mask_columns, mask_identifiers
from ..protocols.registry import ProtocolRegistry
from ..review.models import PlanReview, ReviewAction
from ..review.service import review_plan


class WorkflowError(ValueError):
    """Raised when the workflow cannot continue."""


def run_analysis_workflow(
    user_input: str,
    data: pd.DataFrame,
    outcome: str | None = None,
    group: str | None = None,
    factor2: str | None = None,
    paired_by: str | None = None,
    predictors: tuple[str, ...] = (),
    review_action: ReviewAction | str = ReviewAction.ACCEPT,
    override_protocol_id: str | None = None,
    review_reason: str = "",
    analysis_id: str | None = None,
    audit_dir: str | Path | None = None,
    redact_columns: tuple[str, ...] = (),
    identifier_columns: tuple[str, ...] = (),
    identifier_salt: str = "",
    registry: ProtocolRegistry | None = None,
) -> dict[str, Any]:
    registry = registry or ProtocolRegistry.load_default()
    if redact_columns:
        data = mask_columns(data, redact_columns)
    if identifier_columns:
        data = mask_identifiers(data, identifier_columns, salt=identifier_salt)
    plan = StatisticalPlanner(registry).plan(
        user_input=user_input,
        data=data,
        outcome=outcome,
        group=group,
        factor2=factor2,
        paired_by=paired_by,
        predictors=predictors,
    )
    if plan.status != "ready" or plan.recommended_protocol_id is None:
        raise WorkflowError(plan.reason)

    review = review_plan(
        plan,
        action=review_action,
        override_protocol_id=override_protocol_id,
        reason=review_reason,
        registry=registry,
    )

    request = AnalysisRequest(
        protocol_id=review.final_protocol_id,
        data=data,
        outcome=outcome or _required_outcome(plan, data),
        group=group,
        factor2=factor2,
        paired_by=paired_by,
        predictors=predictors,
    )
    result = run_analysis(request, registry=registry)
    record = create_analysis_record(
        request=request,
        result=result,
        user_input=user_input,
        analysis_id=analysis_id,
        plan=plan,
        human_review=review,
    )

    record_path = None
    if audit_dir is not None:
        record_path = AuditWriter(audit_dir).write(record)

    return {
        "plan": plan,
        "review": review,
        "request": request,
        "result": result,
        "record": record,
        "record_path": record_path,
    }


def _required_outcome(plan: StatisticalPlan, data: pd.DataFrame) -> str:
    numeric_columns = [
        column
        for column in data.columns
        if pd.api.types.is_numeric_dtype(data[column])
    ]
    if not numeric_columns:
        raise WorkflowError("No numeric outcome column could be inferred")
    return numeric_columns[0]
