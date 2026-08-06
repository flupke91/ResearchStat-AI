import pytest

from researchstat.planner import StatisticalPlanner
from researchstat.protocols.registry import ProtocolNotFoundError
from researchstat.review import ReviewAction, explain_plan, review_plan


def _plan():
    return StatisticalPlanner().plan(
        "compare value between two groups",
        data=__import__("pandas").DataFrame(
            {"group": ["A", "A", "B", "B"], "value": [1.0, 2.0, 3.0, 4.0]}
        ),
        outcome="value",
        group="group",
    )


def test_accept_plan():
    plan = _plan()
    review = review_plan(plan, ReviewAction.ACCEPT)

    assert review.recommended_protocol_id == review.final_protocol_id
    assert review.action is ReviewAction.ACCEPT


def test_override_plan_records_reason():
    plan = _plan()
    review = review_plan(
        plan,
        ReviewAction.OVERRIDE,
        override_protocol_id="independent_t_test_welch_v1",
        reason="domain knowledge suggests unequal variance",
    )

    assert review.final_protocol_id == "independent_t_test_welch_v1"
    assert review.reason == "domain knowledge suggests unequal variance"


def test_override_with_invalid_protocol_raises():
    plan = _plan()
    with pytest.raises(ProtocolNotFoundError):
        review_plan(
            plan,
            ReviewAction.OVERRIDE,
            override_protocol_id="not_a_protocol_v1",
        )


def test_explain_plan_returns_text():
    plan = _plan()
    text = explain_plan(plan)

    assert "one_way_anova_tukey_v1" not in text
    assert plan.recommended_protocol_id in text
