"""Models for the human review gate."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ReviewAction(str, Enum):
    ACCEPT = "accept"
    OVERRIDE = "override"


class PlanReview(BaseModel):
    recommended_protocol_id: str
    final_protocol_id: str
    action: ReviewAction
    reason: str = ""
    reviewer: str = "human"
    reviewed_at: datetime
