"""Benchmark scenarios for the statistical planner."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .planner import StatisticalPlanner


@dataclass(frozen=True)
class PlannerScenario:
    name: str
    user_input: str
    data: pd.DataFrame
    expected_protocol_id: str
    outcome: str | None = None
    group: str | None = None
    factor2: str | None = None
    paired_by: str | None = None
    predictors: tuple[str, ...] = ()


@dataclass
class BenchmarkCaseResult:
    name: str
    expected_protocol_id: str
    actual_protocol_id: str | None
    passed: bool
    reason: str = ""


@dataclass
class PlannerBenchmarkResult:
    total: int
    passed: int
    cases: list[BenchmarkCaseResult] = field(default_factory=list)

    @property
    def failed_cases(self) -> list[BenchmarkCaseResult]:
        return [case for case in self.cases if not case.passed]


def _compare_data(groups: int, rows_per_group: int = 12, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = pd.DataFrame(
        {
            "group": [
                f"G{index}"
                for index in range(groups)
                for _ in range(rows_per_group)
            ],
            "value": rng.normal(size=groups * rows_per_group),
        }
    )
    return data


def _paired_data(seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    subjects = list(range(1, 21))
    before = rng.normal(size=20)
    after = before + 0.8 + rng.normal(scale=0.4, size=20)
    return pd.DataFrame(
        {
            "subject": subjects * 2,
            "group": ["before"] * 20 + ["after"] * 20,
            "value": list(before) + list(after),
        }
    )


def _correlation_data(seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = rng.normal(size=40)
    y = 0.6 * x + rng.normal(scale=0.5, size=40)
    return pd.DataFrame({"x": x, "y": y})


def _regression_data(seed: int = 4) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=40)
    x2 = rng.normal(size=40)
    y = 1.0 + 0.8 * x1 - 0.4 * x2 + rng.normal(scale=0.3, size=40)
    return pd.DataFrame({"x1": x1, "x2": x2, "y": y})


def _two_way_data(seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "treatment": ["A", "B"] * 24,
            "sex": ["M"] * 24 + ["F"] * 24,
            "value": rng.normal(size=48),
        }
    )


def build_scenarios() -> list[PlannerScenario]:
    return [
        PlannerScenario(
            name="independent_t_student",
            user_input="compare value between two treatment groups",
            data=_compare_data(2),
            expected_protocol_id="independent_t_test_student_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="independent_t_welch",
            user_input="compare value between two groups with unequal variance",
            data=_compare_data(2),
            expected_protocol_id="independent_t_test_welch_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="mann_whitney",
            user_input="compare skewed scores between two independent groups",
            data=_compare_data(2),
            expected_protocol_id="mann_whitney_u_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="paired_t",
            user_input="compare pre and post paired measurements",
            data=_paired_data(),
            expected_protocol_id="paired_t_test_v1",
            outcome="value",
            group="group",
            paired_by="subject",
        ),
        PlannerScenario(
            name="one_way_anova",
            user_input="compare value across three treatment groups",
            data=_compare_data(3),
            expected_protocol_id="one_way_anova_tukey_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="kruskal_wallis",
            user_input="compare skewed value across three groups",
            data=_compare_data(3),
            expected_protocol_id="kruskal_wallis_dunn_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="two_way_anova",
            user_input="compare value across treatment and sex",
            data=_two_way_data(),
            expected_protocol_id="two_way_anova_v1",
            outcome="value",
            group="treatment",
            factor2="sex",
        ),
        PlannerScenario(
            name="pearson",
            user_input="correlate x and y",
            data=_correlation_data(),
            expected_protocol_id="pearson_correlation_v1",
            outcome="y",
            predictors=("x",),
        ),
        PlannerScenario(
            name="spearman",
            user_input="correlate skewed ranks",
            data=_correlation_data(),
            expected_protocol_id="spearman_correlation_v1",
            outcome="y",
            predictors=("x",),
        ),
        PlannerScenario(
            name="linear_regression",
            user_input="predict y from x1 and x2",
            data=_regression_data(),
            expected_protocol_id="linear_regression_v1",
            outcome="y",
            predictors=("x1", "x2"),
        ),
        PlannerScenario(
            name="descriptive",
            user_input="describe the value variable",
            data=pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}),
            expected_protocol_id="descriptive_v1",
            outcome="value",
        ),
        PlannerScenario(
            name="animal_anova",
            user_input="compare three drugs on mouse tumor size",
            data=_compare_data(3),
            expected_protocol_id="one_way_anova_tukey_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="clinical_two_group",
            user_input="compare HDRS score between treatment groups in a clinical trial",
            data=_compare_data(2),
            expected_protocol_id="independent_t_test_student_v1",
            outcome="value",
            group="group",
        ),
        PlannerScenario(
            name="association_with_data",
            user_input="examine the relationship between x and y",
            data=_correlation_data(),
            expected_protocol_id="pearson_correlation_v1",
            outcome="y",
            predictors=("x",),
        ),
        PlannerScenario(
            name="prediction_with_data",
            user_input="build a prediction model for y",
            data=_regression_data(),
            expected_protocol_id="linear_regression_v1",
            outcome="y",
            predictors=("x1", "x2"),
        ),
    ]


def run_planner_benchmark(
    scenarios: list[PlannerScenario] | None = None,
    planner: StatisticalPlanner | None = None,
) -> PlannerBenchmarkResult:
    scenarios = scenarios or build_scenarios()
    planner = planner or StatisticalPlanner()
    cases: list[BenchmarkCaseResult] = []
    passed = 0
    for scenario in scenarios:
        plan = planner.plan(
            user_input=scenario.user_input,
            data=scenario.data,
            outcome=scenario.outcome,
            group=scenario.group,
            factor2=scenario.factor2,
            paired_by=scenario.paired_by,
            predictors=scenario.predictors,
        )
        actual = plan.recommended_protocol_id
        ok = actual == scenario.expected_protocol_id
        passed += int(ok)
        cases.append(
            BenchmarkCaseResult(
                name=scenario.name,
                expected_protocol_id=scenario.expected_protocol_id,
                actual_protocol_id=actual,
                passed=ok,
                reason=plan.reason if not ok else "",
            )
        )
    return PlannerBenchmarkResult(total=len(scenarios), passed=passed, cases=cases)
