import numpy as np
import pandas as pd
import pytest

from researchstat.engine import AnalysisRequest, is_r_available
from researchstat.validation import cross_validate


pytestmark = pytest.mark.skipif(
    not is_r_available(), reason="R runtime is not available"
)


def assert_cross_valid(request: AnalysisRequest) -> None:
    report = cross_validate(request)
    assert report.passed, "\n".join(
        f"{item.path}: py={item.python_value} r={item.r_value} "
        f"{item.detail}"
        for item in report.failed_comparisons
    )


def test_descriptive_cross_engine():
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="descriptive_v1",
            data=data,
            outcome="value",
        )
    )


def test_independent_t_test_student_cross_engine():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0]
    data = pd.DataFrame(
        {"group": ["A"] * 5 + ["B"] * 5, "value": a + b}
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="independent_t_test_student_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_independent_t_test_welch_cross_engine():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    b = [3.0, 4.0, 5.0, 6.0]
    data = pd.DataFrame(
        {"group": ["A"] * len(a) + ["B"] * len(b), "value": a + b}
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="independent_t_test_welch_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_paired_t_test_cross_engine():
    data = pd.DataFrame(
        {
            "subject": [1, 1, 2, 2, 3, 3, 4, 4],
            "group": ["before", "after"] * 4,
            "value": [2.0, 3.0, 4.0, 5.0, 3.0, 5.0, 4.0, 6.0],
        }
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="paired_t_test_v1",
            data=data,
            outcome="value",
            group="group",
            paired_by="subject",
        )
    )


def test_one_way_anova_cross_engine():
    groups = [
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [2.0, 3.0, 4.0, 5.0, 6.0],
        [4.0, 5.0, 6.0, 7.0, 8.0],
    ]
    data = pd.DataFrame(
        {
            "group": [f"G{i}" for i, values in enumerate(groups) for _ in values],
            "value": [value for values in groups for value in values],
        }
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="one_way_anova_tukey_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_two_way_anova_cross_engine():
    data = pd.DataFrame(
        {
            "outcome": [
                10.0, 12.0, 11.0, 13.0,
                15.0, 17.0, 16.0, 18.0,
                20.0, 22.0, 21.0, 23.0,
            ],
            "factor1": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
            "factor2": ["X", "X", "Y", "Y"] * 3,
        }
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="two_way_anova_v1",
            data=data,
            outcome="outcome",
            group="factor1",
            factor2="factor2",
        )
    )


def test_mann_whitney_cross_engine():
    a = [1.0, 2.0, 4.0, 7.0, 8.0]
    b = [2.0, 3.0, 5.0, 9.0, 10.0]
    data = pd.DataFrame(
        {"group": ["A"] * len(a) + ["B"] * len(b), "value": a + b}
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="mann_whitney_u_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_kruskal_wallis_cross_engine():
    groups = [
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [2.0, 3.0, 4.0, 5.0, 6.0],
        [4.0, 5.0, 6.0, 7.0, 8.0],
    ]
    data = pd.DataFrame(
        {
            "group": [f"G{i}" for i, values in enumerate(groups) for _ in values],
            "value": [value for values in groups for value in values],
        }
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="kruskal_wallis_dunn_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_pearson_cross_engine():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 3.5, 3.0, 5.0, 5.5, 7.0])
    data = pd.DataFrame({"x": x, "y": y})
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="pearson_correlation_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )


def test_spearman_cross_engine():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 6.0, 5.0])
    data = pd.DataFrame({"x": x, "y": y})
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="spearman_correlation_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )


def test_linear_regression_cross_engine():
    rng = np.random.default_rng(3)
    x1 = rng.normal(size=30)
    x2 = rng.normal(size=30)
    y = 2.0 + 1.5 * x1 - 0.5 * x2 + rng.normal(0, 0.5, size=30)
    data = pd.DataFrame({"x1": x1, "x2": x2, "y": y})
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="linear_regression_v1",
            data=data,
            outcome="y",
            predictors=("x1", "x2"),
        )
    )
