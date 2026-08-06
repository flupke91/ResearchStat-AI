"""Human review service."""

from __future__ import annotations

from datetime import datetime, timezone

from ..planner.models import StatisticalPlan
from ..protocols.registry import ProtocolRegistry
from .models import PlanReview, ReviewAction


class ReviewError(ValueError):
    """Raised when a plan cannot be reviewed."""


def review_plan(
    plan: StatisticalPlan,
    action: ReviewAction | str,
    override_protocol_id: str | None = None,
    reason: str = "",
    registry: ProtocolRegistry | None = None,
) -> PlanReview:
    if isinstance(action, str):
        action = ReviewAction(action)
    if plan.recommended_protocol_id is None:
        raise ReviewError("Plan has no recommended protocol to review")

    registry = registry or ProtocolRegistry.load_default()
    if action is ReviewAction.ACCEPT:
        final_protocol_id = plan.recommended_protocol_id
    else:
        if not override_protocol_id:
            raise ReviewError("Override requires a final protocol id")
        final_protocol_id = override_protocol_id

    registry.get(final_protocol_id)
    return PlanReview(
        recommended_protocol_id=plan.recommended_protocol_id,
        final_protocol_id=final_protocol_id,
        action=action,
        reason=reason,
        reviewer="human",
        reviewed_at=datetime.now(timezone.utc),
    )


def explain_plan(
    plan: StatisticalPlan,
    registry: ProtocolRegistry | None = None,
) -> str:
    registry = registry or ProtocolRegistry.load_default()
    if plan.recommended_protocol_id is None:
        return "The planner needs more information before it can recommend a protocol."
    protocol = registry.get(plan.recommended_protocol_id)
    assumptions = ", ".join(plan.assumptions_to_check) or "none declared"
    return (
        f"Recommended protocol {protocol.id} because {plan.reason} "
        f"Assumptions to check: {assumptions}."
    )
