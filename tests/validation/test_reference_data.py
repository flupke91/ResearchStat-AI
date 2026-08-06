from pathlib import Path

import pandas as pd
import pytest

from researchstat.engine import AnalysisRequest, is_r_available, run_analysis
from researchstat.validation import cross_validate


VALIDATION_DIR = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "validation"
)
R_DATASETS = VALIDATION_DIR / "r_datasets"


def assert_cross_valid(request: AnalysisRequest) -> None:
    report = cross_validate(request)
    assert report.passed, "\n".join(
        f"{item.path}: py={item.python_value} r={item.r_value} "
        f"{item.detail}"
        for item in report.failed_comparisons
    )


def test_nist_norris_linear_regression_certified_values():
    lines = (VALIDATION_DIR / "nist_norris.dat").read_text(encoding="utf-8").splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("Data:       y          x")
    ) + 1
    rows = []
    for line in lines[start:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append((float(parts[0]), float(parts[1])))
    data = pd.DataFrame(rows, columns=["y", "x"])

    result = run_analysis(
        AnalysisRequest(
            protocol_id="linear_regression_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )

    assert result.statistics["coefficients"]["const"]["estimate"] == pytest.approx(
        -0.262323073774029, rel=1e-10
    )
    assert result.statistics["coefficients"]["x"]["estimate"] == pytest.approx(
        1.00211681802045, rel=1e-10
    )
    assert result.statistics["r_squared"] == pytest.approx(
        0.999993745883712, rel=1e-10
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_nist_norris_cross_engine():
    lines = (VALIDATION_DIR / "nist_norris.dat").read_text(encoding="utf-8").splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("Data:       y          x")
    ) + 1
    rows = []
    for line in lines[start:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append((float(parts[0]), float(parts[1])))
    data = pd.DataFrame(rows, columns=["y", "x"])
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="linear_regression_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_r_dataset_plantgrowth_one_way_anova_cross_engine():
    data = pd.read_csv(R_DATASETS / "PlantGrowth.csv")
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="one_way_anova_tukey_v1",
            data=data,
            outcome="weight",
            group="group",
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_r_dataset_sleep_paired_t_test_cross_engine():
    data = pd.read_csv(R_DATASETS / "sleep.csv")
    data["group"] = data["group"].astype(str)
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="paired_t_test_v1",
            data=data,
            outcome="extra",
            group="group",
            paired_by="ID",
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_r_dataset_iris_pearson_cross_engine():
    data = pd.read_csv(R_DATASETS / "iris.csv")
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="pearson_correlation_v1",
            data=data,
            outcome="Sepal.Width",
            predictors=("Sepal.Length",),
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_r_dataset_mtcars_linear_regression_cross_engine():
    data = pd.read_csv(R_DATASETS / "mtcars.csv")
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="linear_regression_v1",
            data=data,
            outcome="mpg",
            predictors=("wt",),
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_r_dataset_npk_two_way_anova_cross_engine():
    data = pd.read_csv(R_DATASETS / "npk.csv")
    data["N"] = data["N"].astype(str)
    data["P"] = data["P"].astype(str)
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="two_way_anova_v1",
            data=data,
            outcome="yield",
            group="N",
            factor2="P",
        )
    )


@pytest.mark.skipif(not is_r_available(), reason="R runtime is not available")
def test_heavy_ties_cross_engine():
    data = pd.DataFrame(
        {
            "group": ["A"] * 12 + ["B"] * 12,
            "value": [
                1.0, 1.0, 2.0, 2.0, 2.0, 3.0,
                3.0, 4.0, 4.0, 5.0, 5.0, 5.0,
                2.0, 2.0, 3.0, 3.0, 3.0, 4.0,
                4.0, 5.0, 6.0, 6.0, 7.0, 8.0,
            ],
        }
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="mann_whitney_u_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    assert_cross_valid(
        AnalysisRequest(
            protocol_id="kruskal_wallis_dunn_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )


def test_unbalanced_two_way_anova_records_warning():
    data = pd.DataFrame(
        {
            "outcome": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "factor1": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "factor2": ["X", "X", "X", "Y", "X", "Y", "Y", "Y"],
        }
    )
    result = run_analysis(
        AnalysisRequest(
            protocol_id="two_way_anova_v1",
            data=data,
            outcome="outcome",
            group="factor1",
            factor2="factor2",
        )
    )

    assert any("Unbalanced design" in warning for warning in result.warnings)
