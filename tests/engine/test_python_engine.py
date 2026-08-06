import numpy as np
import pandas as pd
import pytest
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

from researchstat.engine import AnalysisRequest, run_analysis
from researchstat.protocols.registry import ProtocolNotFoundError


def test_descriptive_statistics():
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
    result = run_analysis(
        AnalysisRequest(
            protocol_id="descriptive_v1",
            data=data,
            outcome="value",
        )
    )

    assert result.statistics["n"] == 5
    assert result.statistics["mean"] == pytest.approx(3.0)
    assert result.statistics["std"] == pytest.approx(
        np.std([1, 2, 3, 4, 5], ddof=1)
    )


def test_independent_t_test_matches_scipy():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0]
    data = pd.DataFrame(
        {
            "group": ["A"] * len(a) + ["B"] * len(b),
            "value": a + b,
        }
    )
    result = run_analysis(
        AnalysisRequest(
            protocol_id="independent_t_test_student_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    expected = stats.ttest_ind(a, b, equal_var=True)

    assert result.statistics["t"] == pytest.approx(expected.statistic)
    assert result.p_values["two_sided"] == pytest.approx(expected.pvalue)


def test_paired_t_test_matches_scipy():
    data = pd.DataFrame(
        {
            "subject": [1, 1, 2, 2, 3, 3, 4, 4],
            "group": ["before", "after"] * 4,
            "value": [2.0, 3.0, 4.0, 5.0, 3.0, 5.0, 4.0, 6.0],
        }
    )
    result = run_analysis(
        AnalysisRequest(
            protocol_id="paired_t_test_v1",
            data=data,
            outcome="value",
            group="group",
            paired_by="subject",
        )
    )
    labels = result.metadata["groups"]
    first = data.loc[data["group"] == labels[0], "value"].to_numpy()
    second = data.loc[data["group"] == labels[1], "value"].to_numpy()
    expected = stats.ttest_rel(first, second)

    assert result.statistics["t"] == pytest.approx(expected.statistic)
    assert result.p_values["two_sided"] == pytest.approx(expected.pvalue)


def test_one_way_anova_matches_scipy():
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
    result = run_analysis(
        AnalysisRequest(
            protocol_id="one_way_anova_tukey_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    expected = stats.f_oneway(*groups)

    assert result.statistics["F"] == pytest.approx(expected.statistic)
    assert result.p_values["overall"] == pytest.approx(expected.pvalue)
    assert len(result.p_values["pairwise"]) == 3
    assert 0 <= result.effect_size["eta_squared"] <= 1


def test_two_way_anova_matches_statsmodels():
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
    result = run_analysis(
        AnalysisRequest(
            protocol_id="two_way_anova_v1",
            data=data,
            outcome="outcome",
            group="factor1",
            factor2="factor2",
        )
    )
    model = ols(
        "outcome ~ C(factor1, Sum) * C(factor2, Sum)", data=data
    ).fit()
    anova = anova_lm(model, typ=3)

    assert result.p_values["factor1"] == pytest.approx(
        anova.loc["C(factor1, Sum)", "PR(>F)"]
    )
    assert result.p_values["factor2"] == pytest.approx(
        anova.loc["C(factor2, Sum)", "PR(>F)"]
    )
    assert result.p_values["interaction"] == pytest.approx(
        anova.loc["C(factor1, Sum):C(factor2, Sum)", "PR(>F)"]
    )


def test_mann_whitney_matches_scipy():
    a = [1.0, 2.0, 4.0, 7.0, 8.0]
    b = [2.0, 3.0, 5.0, 9.0, 10.0]
    data = pd.DataFrame(
        {"group": ["A"] * len(a) + ["B"] * len(b), "value": a + b}
    )
    result = run_analysis(
        AnalysisRequest(
            protocol_id="mann_whitney_u_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    expected = stats.mannwhitneyu(a, b, alternative="two-sided", method="auto")

    assert result.statistics["U"] == pytest.approx(expected.statistic)
    assert result.p_values["two_sided"] == pytest.approx(expected.pvalue)


def test_kruskal_wallis_matches_scipy():
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
    result = run_analysis(
        AnalysisRequest(
            protocol_id="kruskal_wallis_dunn_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    expected = stats.kruskal(*groups)

    assert result.statistics["H"] == pytest.approx(expected.statistic)
    assert result.p_values["overall"] == pytest.approx(expected.pvalue)
    assert len(result.p_values["pairwise"]) == 3


def test_pearson_matches_scipy():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 3.5, 3.0, 5.0, 5.5, 7.0])
    data = pd.DataFrame({"x": x, "y": y})
    result = run_analysis(
        AnalysisRequest(
            protocol_id="pearson_correlation_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )
    expected = stats.pearsonr(x, y)

    assert result.statistics["r"] == pytest.approx(expected.statistic)
    assert result.p_values["two_sided"] == pytest.approx(expected.pvalue)


def test_spearman_matches_scipy():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 6.0, 5.0])
    data = pd.DataFrame({"x": x, "y": y})
    result = run_analysis(
        AnalysisRequest(
            protocol_id="spearman_correlation_v1",
            data=data,
            outcome="y",
            predictors=("x",),
        )
    )
    expected = stats.spearmanr(x, y)

    assert result.statistics["rho"] == pytest.approx(expected.statistic)
    assert result.p_values["two_sided"] == pytest.approx(expected.pvalue)


def test_linear_regression_matches_statsmodels():
    rng = np.random.default_rng(3)
    x1 = rng.normal(size=30)
    x2 = rng.normal(size=30)
    y = 2.0 + 1.5 * x1 - 0.5 * x2 + rng.normal(0, 0.5, size=30)
    data = pd.DataFrame({"x1": x1, "x2": x2, "y": y})
    result = run_analysis(
        AnalysisRequest(
            protocol_id="linear_regression_v1",
            data=data,
            outcome="y",
            predictors=("x1", "x2"),
        )
    )
    model = sm.OLS(y, sm.add_constant(data[["x1", "x2"]])).fit()

    assert result.statistics["r_squared"] == pytest.approx(model.rsquared)
    assert result.statistics["coefficients"]["x1"]["estimate"] == pytest.approx(
        model.params["x1"]
    )
    assert result.statistics["coefficients"]["x2"]["estimate"] == pytest.approx(
        model.params["x2"]
    )


def test_unknown_protocol_raises():
    data = pd.DataFrame({"value": [1.0, 2.0]})
    with pytest.raises(ProtocolNotFoundError):
        run_analysis(
            AnalysisRequest(
                protocol_id="not_a_protocol_v1",
                data=data,
                outcome="value",
            )
        )


def test_complete_case_missing_data_warning():
    data = pd.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B"],
            "value": [1.0, 2.0, np.nan, 3.0, 4.0],
        }
    )
    result = run_analysis(
        AnalysisRequest(
            protocol_id="independent_t_test_student_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )

    assert any("complete_case removed 1 row(s)" in w for w in result.warnings)


def test_alpha_override_is_recorded():
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    result = run_analysis(
        AnalysisRequest(
            protocol_id="descriptive_v1",
            data=data,
            outcome="value",
            alpha=0.01,
        )
    )

    assert any("alpha overridden" in w for w in result.warnings)
