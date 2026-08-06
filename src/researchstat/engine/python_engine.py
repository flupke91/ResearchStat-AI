"""Python implementation of the V1 statistical execution engine."""

from __future__ import annotations

import platform
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
import scipy
import scikit_posthocs as sp
import statsmodels.api as sm
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from ..protocols.registry import ProtocolRegistry
from ..protocols.schema import Protocol, StatisticalMethod
from .models import AnalysisRequest, AnalysisResult, AssumptionCheck, EngineInfo


class EngineError(Exception):
    """Base error for the execution engine."""


class InvalidAnalysisInputError(EngineError, ValueError):
    """Raised when an analysis request cannot be executed."""


class UnsupportedProtocolError(EngineError, ValueError):
    """Raised when a protocol method has no Python implementation."""


def python_engine_info() -> EngineInfo:
    libraries = {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "statsmodels": sm.__version__,
        "scikit_posthocs": sp.__version__,
    }
    return EngineInfo(
        name="python",
        version=platform.python_version(),
        libraries=libraries,
    )


class PythonEngine:
    """Protocol-bound Python execution engine."""

    def run(
        self,
        request: AnalysisRequest,
        registry: ProtocolRegistry | None = None,
    ) -> AnalysisResult:
        return run_analysis(request, registry=registry)


def run_analysis(
    request: AnalysisRequest,
    registry: ProtocolRegistry | None = None,
) -> AnalysisResult:
    registry = registry or ProtocolRegistry.load_default()
    protocol = registry.get(request.protocol_id)

    alpha = request.alpha if request.alpha is not None else protocol.alpha
    warnings: list[str] = []
    if request.alpha is not None and request.alpha != protocol.alpha:
        warnings.append(
            f"alpha overridden from {protocol.alpha} to {request.alpha}"
        )

    handlers: dict[StatisticalMethod, Any] = {
        StatisticalMethod.DESCRIPTIVE: _run_descriptive,
        StatisticalMethod.INDEPENDENT_T_TEST: _run_independent_t_test,
        StatisticalMethod.PAIRED_T_TEST: _run_paired_t_test,
        StatisticalMethod.ONE_WAY_ANOVA: _run_one_way_anova,
        StatisticalMethod.TWO_WAY_ANOVA: _run_two_way_anova,
        StatisticalMethod.MANN_WHITNEY_U: _run_mann_whitney_u,
        StatisticalMethod.KRUSKAL_WALLIS: _run_kruskal_wallis,
        StatisticalMethod.PEARSON_CORRELATION: _run_pearson,
        StatisticalMethod.SPEARMAN_CORRELATION: _run_spearman,
        StatisticalMethod.LINEAR_REGRESSION: _run_linear_regression,
    }

    handler = handlers.get(protocol.method)
    if handler is None:
        raise UnsupportedProtocolError(
            f"No Python handler for method: {protocol.method.value}"
        )

    result = handler(request, protocol, alpha)
    result.warnings = warnings + result.warnings
    return result


def _prepare_columns(
    request: AnalysisRequest, columns: Sequence[str]
) -> tuple[pd.DataFrame, list[str]]:
    missing = [column for column in columns if column not in request.data.columns]
    if missing:
        raise InvalidAnalysisInputError(
            f"Missing required columns: {', '.join(missing)}"
        )

    work = request.data.copy()
    if request.outcome in work.columns:
        work[request.outcome] = pd.to_numeric(
            work[request.outcome], errors="coerce"
        )

    before = len(work)
    work = work.dropna(subset=columns)
    warnings: list[str] = []
    dropped = before - len(work)
    if dropped:
        warnings.append(f"complete_case removed {dropped} row(s)")
    return work, warnings


def _group_values(
    work: pd.DataFrame, group: str, outcome: str, min_groups: int = 2
) -> dict[str, np.ndarray]:
    if group is None:
        raise InvalidAnalysisInputError("This protocol requires a group column")
    labels = sorted({str(value) for value in pd.unique(work[group])})
    if len(labels) < min_groups:
        raise InvalidAnalysisInputError(
            f"Expected at least {min_groups} groups, found {len(labels)}"
        )
    groups: dict[str, np.ndarray] = {}
    for label in labels:
        mask = work[group].astype(str) == label
        values = work.loc[mask, outcome].to_numpy(dtype=float)
        if len(values) < 2:
            raise InvalidAnalysisInputError(
                f"Group '{label}' needs at least 2 observations"
            )
        groups[label] = values
    return groups


def _paired_wide(
    work: pd.DataFrame, request: AnalysisRequest
) -> pd.DataFrame:
    if request.group is None or request.paired_by is None:
        raise InvalidAnalysisInputError(
            "Paired analysis requires both group and paired_by columns"
        )
    pivot = work.pivot_table(
        index=request.paired_by,
        columns=request.group,
        values=request.outcome,
        aggfunc="first",
    )
    pivot.columns = [str(column) for column in pivot.columns]
    pivot = pivot.dropna()
    if pivot.shape[1] != 2:
        raise InvalidAnalysisInputError(
            f"Paired analysis requires exactly 2 groups, found {pivot.shape[1]}"
        )
    if len(pivot) < 2:
        raise InvalidAnalysisInputError(
            "Paired analysis requires at least 2 complete pairs"
        )
    return pivot


def _shapiro_checks(
    groups: Mapping[str, Sequence[float]], alpha: float
) -> list[AssumptionCheck]:
    checks: list[AssumptionCheck] = []
    for label, values in groups.items():
        values = np.asarray(values, dtype=float)
        if len(values) < 3:
            checks.append(
                AssumptionCheck(
                    name=f"shapiro_wilk:{label}",
                    passed=None,
                    detail="n<3, test not computed",
                )
            )
            continue
        statistic, p_value = stats.shapiro(values)
        checks.append(
            AssumptionCheck(
                name=f"shapiro_wilk:{label}",
                passed=bool(p_value >= alpha),
                statistic=float(statistic),
                p_value=float(p_value),
            )
        )
    return checks


def _levene_check(
    groups: Mapping[str, Sequence[float]], alpha: float
) -> AssumptionCheck | None:
    if len(groups) < 2:
        return None
    if any(len(np.asarray(values, dtype=float)) < 3 for values in groups.values()):
        return AssumptionCheck(
            name="levene_equal_variance",
            passed=None,
            detail="requires at least 3 observations per group, test not computed",
        )
    statistic, p_value = stats.levene(
        *[np.asarray(values, dtype=float) for values in groups.values()],
        center="median",
    )
    return AssumptionCheck(
        name="levene_equal_variance",
        passed=bool(p_value >= alpha),
        statistic=float(statistic),
        p_value=float(p_value),
    )


def _assumption_warnings(
    checks: Sequence[AssumptionCheck], warnings: list[str]
) -> None:
    for check in checks:
        if check.passed is False:
            p_text = (
                f"p={check.p_value:.6g}" if check.p_value is not None else "n/a"
            )
            warnings.append(
                f"Assumption check '{check.name}' may be violated ({p_text})"
            )


def _build_result(
    protocol: Protocol,
    statistics: dict[str, Any],
    p_values: dict[str, Any],
    effect_size: dict[str, float],
    assumptions: Sequence[AssumptionCheck],
    warnings: Sequence[str],
    parameters: dict[str, Any],
    metadata: dict[str, Any],
) -> AnalysisResult:
    return AnalysisResult(
        protocol_id=protocol.id,
        method=protocol.method.value,
        engine=python_engine_info(),
        statistics=statistics,
        p_values=p_values,
        effect_size=effect_size,
        assumptions=list(assumptions),
        warnings=list(warnings),
        parameters=parameters,
        metadata=metadata,
    )


def _run_descriptive(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(request, [request.outcome])
    values = work[request.outcome].to_numpy(dtype=float)
    n = len(values)
    if n == 0:
        raise InvalidAnalysisInputError("Descriptive analysis needs at least 1 value")

    mean = float(np.mean(values))
    median = float(np.median(values))
    q1, q3 = np.percentile(values, [25, 75])
    statistics: dict[str, Any] = {
        "n": n,
        "mean": mean,
        "median": median,
        "std": float(np.std(values, ddof=1)),
        "q1": float(q1),
        "q3": float(q3),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }
    if n >= 2:
        sem = stats.sem(values)
        t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)
        statistics["sem"] = float(sem)
        statistics["ci95_lower"] = float(mean - t_crit * sem)
        statistics["ci95_upper"] = float(mean + t_crit * sem)
    else:
        warnings.append("Descriptive analysis with n=1 cannot compute SEM/CI")

    return _build_result(
        protocol=protocol,
        statistics=statistics,
        p_values={},
        effect_size={},
        assumptions=[],
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"variable": request.outcome},
    )


def _run_independent_t_test(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(request, [request.outcome, request.group])
    groups = _group_values(work, request.group, request.outcome)
    if len(groups) != 2:
        raise InvalidAnalysisInputError(
            "Independent t-test requires exactly 2 groups"
        )

    labels = list(groups)
    a, b = groups[labels[0]], groups[labels[1]]
    equal_var = protocol.assumptions.variance.value == "equal_variance"
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=equal_var)

    n1, n2 = len(a), len(b)
    mean1, mean2 = float(np.mean(a)), float(np.mean(b))
    sd1, sd2 = float(np.std(a, ddof=1)), float(np.std(b, ddof=1))

    if equal_var:
        df = n1 + n2 - 2
        pooled_sd = np.sqrt(
            ((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / df
        )
        cohens_d = (mean1 - mean2) / pooled_sd
    else:
        variance_numer = sd1**2 / n1 + sd2**2 / n2
        df = (
            variance_numer**2
            / ((sd1**2 / n1) ** 2 / (n1 - 1) + (sd2**2 / n2) ** 2 / (n2 - 1))
        )
        cohens_d = (mean1 - mean2) / np.sqrt((sd1**2 + sd2**2) / 2)

    assumptions = _shapiro_checks(
        {f"group:{labels[0]}": a, f"group:{labels[1]}": b}, alpha
    )
    if equal_var:
        levene = _levene_check(
            {f"group:{labels[0]}": a, f"group:{labels[1]}": b}, alpha
        )
        if levene is not None:
            assumptions.append(levene)
    _assumption_warnings(assumptions, warnings)

    return _build_result(
        protocol=protocol,
        statistics={
            "t": float(t_stat),
            "df": float(df),
            "mean_difference": float(mean1 - mean2),
            "mean_group1": mean1,
            "mean_group2": mean2,
            "sd_group1": sd1,
            "sd_group2": sd2,
            "n_group1": n1,
            "n_group2": n2,
        },
        p_values={"two_sided": float(p_value)},
        effect_size={"cohens_d": float(cohens_d)},
        assumptions=assumptions,
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"groups": labels},
    )


def _run_paired_t_test(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(
        request, [request.outcome, request.group, request.paired_by]
    )
    pivot = _paired_wide(work, request)
    labels = list(pivot.columns)
    a = pivot[labels[0]].to_numpy(dtype=float)
    b = pivot[labels[1]].to_numpy(dtype=float)
    t_stat, p_value = stats.ttest_rel(a, b)
    differences = a - b
    cohens_d = float(np.mean(differences) / np.std(differences, ddof=1))

    assumptions = _shapiro_checks({"paired_differences": differences}, alpha)
    _assumption_warnings(assumptions, warnings)

    return _build_result(
        protocol=protocol,
        statistics={
            "t": float(t_stat),
            "df": float(len(a) - 1),
            "mean_difference": float(np.mean(differences)),
            "sd_difference": float(np.std(differences, ddof=1)),
            "n_pairs": int(len(a)),
        },
        p_values={"two_sided": float(p_value)},
        effect_size={"cohens_d": cohens_d},
        assumptions=assumptions,
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"groups": labels},
    )


def _run_one_way_anova(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(request, [request.outcome, request.group])
    groups = _group_values(work, request.group, request.outcome)
    arrays = list(groups.values())
    labels = list(groups)
    f_stat, p_value = stats.f_oneway(*arrays)

    n_total = sum(len(values) for values in arrays)
    grand_mean = float(np.mean(np.concatenate(arrays)))
    ss_between = float(
        sum(len(values) * (float(np.mean(values)) - grand_mean) ** 2 for values in arrays)
    )
    ss_total = float(
        sum(((values - grand_mean) ** 2).sum() for values in arrays)
    )
    ss_within = ss_total - ss_between
    df1 = len(arrays) - 1
    df2 = n_total - len(arrays)
    eta_squared = ss_between / ss_total if ss_total > 0 else float("nan")

    all_values = np.concatenate(arrays)
    all_labels = np.concatenate(
        [np.repeat(label, len(values)) for label, values in zip(labels, arrays)]
    )
    tukey = pairwise_tukeyhsd(all_values, all_labels, alpha=alpha)
    unique = [str(value) for value in tukey.groupsunique]
    pair_labels = [
        (unique[i], unique[j])
        for i in range(len(unique))
        for j in range(i + 1, len(unique))
    ]
    pairwise: dict[str, Any] = {}
    for (g1, g2), diff, pair_p, (lo, hi) in zip(
        pair_labels, tukey.meandiffs, tukey.pvalues, tukey.confint
    ):
        pairwise[f"{g1}-{g2}"] = {
            "mean_difference": float(diff),
            "p_value": float(pair_p),
            "ci_lower": float(lo),
            "ci_upper": float(hi),
        }

    assumptions = _shapiro_checks(
        {f"group:{label}": values for label, values in groups.items()}, alpha
    )
    levene = _levene_check(groups, alpha)
    if levene is not None:
        assumptions.append(levene)
    _assumption_warnings(assumptions, warnings)

    return _build_result(
        protocol=protocol,
        statistics={
            "F": float(f_stat),
            "df1": df1,
            "df2": df2,
            "n_total": n_total,
            "ss_between": ss_between,
            "ss_within": ss_within,
            "ss_total": ss_total,
            "ms_between": ss_between / df1,
            "ms_within": ss_within / df2,
        },
        p_values={"overall": float(p_value), "pairwise": pairwise},
        effect_size={"eta_squared": eta_squared},
        assumptions=assumptions,
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"groups": labels},
    )


def _run_two_way_anova(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    if request.factor2 is None:
        raise InvalidAnalysisInputError("Two-way ANOVA requires factor2")
    work, warnings = _prepare_columns(
        request, [request.outcome, request.group, request.factor2]
    )
    df = work.copy()
    df["_outcome"] = df[request.outcome].astype(float)
    df["_factor1"] = df[request.group].astype(str)
    df["_factor2"] = df[request.factor2].astype(str)

    cell_counts = df.groupby(["_factor1", "_factor2"], observed=True).size()
    if cell_counts.nunique() > 1:
        warnings.append(
            "Unbalanced design detected; Type III sums of squares are reported"
        )
    if len(df) < 4:
        raise InvalidAnalysisInputError(
            "Two-way ANOVA needs at least 4 complete observations"
        )

    model = ols(
        "_outcome ~ C(_factor1, Sum) * C(_factor2, Sum)", data=df
    ).fit()
    anova = anova_lm(model, typ=3)
    residual_ss = float(anova.loc["Residual", "sum_sq"])
    term_map = {
        "C(_factor1, Sum)": "factor1",
        "C(_factor2, Sum)": "factor2",
        "C(_factor1, Sum):C(_factor2, Sum)": "interaction",
    }

    statistics: dict[str, Any] = {
        "n": int(len(df)),
        "residual_df": int(anova.loc["Residual", "df"]),
        "residual_ss": residual_ss,
    }
    p_values: dict[str, Any] = {}
    effect_size: dict[str, float] = {}
    for term, label in term_map.items():
        row = anova.loc[term]
        ss = float(row["sum_sq"])
        statistics[f"F_{label}"] = float(row["F"])
        statistics[f"df_{label}"] = int(row["df"])
        statistics[f"ss_{label}"] = ss
        p_values[label] = float(row["PR(>F)"])
        effect_size[f"partial_eta_squared_{label}"] = ss / (ss + residual_ss)

    residuals = model.resid.to_numpy(dtype=float)
    assumptions = _shapiro_checks({"residuals": residuals}, alpha)
    interaction = df["_factor1"] + "_" + df["_factor2"]
    levene_groups = {
        label: df.loc[interaction == label, "_outcome"].to_numpy(dtype=float)
        for label in sorted(pd.unique(interaction))
    }
    levene = _levene_check(levene_groups, alpha)
    if levene is not None:
        assumptions.append(levene)
    _assumption_warnings(assumptions, warnings)

    return _build_result(
        protocol=protocol,
        statistics=statistics,
        p_values=p_values,
        effect_size=effect_size,
        assumptions=assumptions,
        warnings=warnings,
        parameters={
            "alpha": alpha,
            "missing_policy": "complete_case",
            "type_iii_ss": True,
        },
        metadata={"factor1": request.group, "factor2": request.factor2},
    )


def _run_mann_whitney_u(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(request, [request.outcome, request.group])
    groups = _group_values(work, request.group, request.outcome)
    if len(groups) != 2:
        raise InvalidAnalysisInputError(
            "Mann-Whitney U requires exactly 2 groups"
        )

    labels = list(groups)
    a, b = groups[labels[0]], groups[labels[1]]
    u_stat, p_value = stats.mannwhitneyu(
        a, b, alternative="two-sided", method="auto"
    )
    n1, n2 = len(a), len(b)
    rank_biserial = 1 - (2 * u_stat) / (n1 * n2)

    return _build_result(
        protocol=protocol,
        statistics={
            "U": float(u_stat),
            "n_group1": n1,
            "n_group2": n2,
        },
        p_values={"two_sided": float(p_value)},
        effect_size={"rank_biserial": float(rank_biserial)},
        assumptions=[],
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"groups": labels},
    )


def _run_kruskal_wallis(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    work, warnings = _prepare_columns(request, [request.outcome, request.group])
    groups = _group_values(work, request.group, request.outcome)
    arrays = list(groups.values())
    labels = list(groups)
    h_stat, p_value = stats.kruskal(*arrays)
    n_total = sum(len(values) for values in arrays)
    epsilon_squared = h_stat / (n_total - 1) if n_total > 1 else float("nan")

    frame = pd.DataFrame(
        {
            "value": np.concatenate(arrays),
            "group": np.concatenate(
                [np.repeat(label, len(values)) for label, values in zip(labels, arrays)]
            ),
        }
    )
    posthoc = sp.posthoc_dunn(
        frame,
        val_col="value",
        group_col="group",
        p_adjust="holm",
    )
    pairwise: dict[str, float] = {}
    for i, g1 in enumerate(posthoc.index):
        for g2 in posthoc.columns[i + 1 :]:
            pairwise[f"{g1}-{g2}"] = float(posthoc.loc[g1, g2])

    return _build_result(
        protocol=protocol,
        statistics={
            "H": float(h_stat),
            "df": len(arrays) - 1,
            "n_total": n_total,
        },
        p_values={"overall": float(p_value), "pairwise": pairwise},
        effect_size={"epsilon_squared": epsilon_squared},
        assumptions=[],
        warnings=warnings,
        parameters={
            "alpha": alpha,
            "missing_policy": "complete_case",
            "posthoc_adjustment": "holm",
        },
        metadata={"groups": labels},
    )


def _run_pearson(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    if len(request.predictors) != 1:
        raise InvalidAnalysisInputError(
            "Pearson correlation requires exactly one predictor variable"
        )
    x_name = request.predictors[0]
    work, warnings = _prepare_columns(request, [request.outcome, x_name])
    x = work[x_name].to_numpy(dtype=float)
    y = work[request.outcome].to_numpy(dtype=float)
    r, p_value = stats.pearsonr(x, y)

    return _build_result(
        protocol=protocol,
        statistics={"r": float(r), "n": int(len(x))},
        p_values={"two_sided": float(p_value)},
        effect_size={"pearson_r": float(r)},
        assumptions=[],
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"x": x_name, "y": request.outcome},
    )


def _run_spearman(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    if len(request.predictors) != 1:
        raise InvalidAnalysisInputError(
            "Spearman correlation requires exactly one predictor variable"
        )
    x_name = request.predictors[0]
    work, warnings = _prepare_columns(request, [request.outcome, x_name])
    x = work[x_name].to_numpy(dtype=float)
    y = work[request.outcome].to_numpy(dtype=float)
    rho, p_value = stats.spearmanr(x, y)

    return _build_result(
        protocol=protocol,
        statistics={"rho": float(rho), "n": int(len(x))},
        p_values={"two_sided": float(p_value)},
        effect_size={"spearman_rho": float(rho)},
        assumptions=[],
        warnings=warnings,
        parameters={"alpha": alpha, "missing_policy": "complete_case"},
        metadata={"x": x_name, "y": request.outcome},
    )


def _run_linear_regression(
    request: AnalysisRequest, protocol: Protocol, alpha: float
) -> AnalysisResult:
    if not request.predictors:
        raise InvalidAnalysisInputError(
            "Linear regression requires at least one predictor"
        )
    columns = [request.outcome, *request.predictors]
    work, warnings = _prepare_columns(request, columns)
    y = work[request.outcome]
    x = sm.add_constant(work[list(request.predictors)], has_constant="add")
    model = sm.OLS(y, x).fit()

    coefficients: dict[str, Any] = {}
    for name in model.params.index:
        ci_lower, ci_upper = model.conf_int().loc[name]
        coefficients[str(name)] = {
            "estimate": float(model.params[name]),
            "std_error": float(model.bse[name]),
            "t": float(model.tvalues[name]),
            "p_value": float(model.pvalues[name]),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
        }

    residuals = model.resid.to_numpy(dtype=float)
    assumptions = _shapiro_checks({"residuals": residuals}, alpha)
    _assumption_warnings(assumptions, warnings)

    return _build_result(
        protocol=protocol,
        statistics={
            "n": int(model.nobs),
            "k": int(model.df_model) + 1,
            "residual_df": int(model.df_resid),
            "r_squared": float(model.rsquared),
            "adjusted_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "residual_std_error": float(np.sqrt(model.mse_resid)),
            "coefficients": coefficients,
        },
        p_values={
            "overall_f": float(model.f_pvalue),
            "coefficients": {
                name: coefficients[name]["p_value"] for name in coefficients
            },
        },
        effect_size={"r_squared": float(model.rsquared)},
        assumptions=assumptions,
        warnings=warnings,
        parameters={
            "alpha": alpha,
            "missing_policy": "complete_case",
            "include_intercept": True,
        },
        metadata={"predictors": list(request.predictors)},
    )
