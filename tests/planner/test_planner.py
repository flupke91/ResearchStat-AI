import pandas as pd

from researchstat.planner import StatisticalPlanner, run_planner_benchmark


def test_planner_benchmark_all_scenarios_pass():
    result = run_planner_benchmark()

    assert result.total == 15
    assert result.passed == 15, "\n".join(
        f"{case.name}: expected {case.expected_protocol_id}, "
        f"got {case.actual_protocol_id}"
        for case in result.failed_cases
    )


def test_planner_animal_anova_uses_protocol_registry():
    data = pd.DataFrame(
        {
            "group": ["ctrl", "trt1", "trt2"] * 4,
            "value": [1.0, 2.0, 4.0] * 4,
        }
    )
    plan = StatisticalPlanner().plan(
        "compare three drugs on mouse tumor size",
        data=data,
        outcome="value",
        group="group",
    )

    assert plan.status == "ready"
    assert plan.recommended_protocol_id == "one_way_anova_tukey_v1"
    assert plan.experiment_type == "Animal study"
    assert "shapiro_wilk" in plan.assumptions_to_check


def test_planner_needs_more_info_for_survival():
    plan = StatisticalPlanner().plan("survival analysis of time to event")

    assert plan.status == "needs_more_info"
    assert plan.recommended_protocol_id is None


def test_planner_correlation_prefers_spearman_for_rank_data():
    data = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 1, 4, 3]})
    plan = StatisticalPlanner().plan(
        "correlate skewed ranks",
        data=data,
        outcome="y",
        predictors=("x",),
    )

    assert plan.recommended_protocol_id == "spearman_correlation_v1"
