"""Reusable renderers for the professional figure engine."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from statannotations.Annotator import Annotator

from ..engine.models import AnalysisResult


def _pairwise_annotations(
    ax: plt.Axes,
    data: pd.DataFrame,
    group: str,
    y: str,
    analysis_result: AnalysisResult | None,
) -> None:
    if analysis_result is None:
        return
    pairwise = analysis_result.p_values.get("pairwise")
    if not isinstance(pairwise, dict) or not pairwise:
        return

    labels = [str(value) for value in sorted(pd.unique(data[group]))]
    pairs: list[tuple[str, str]] = []
    pvalues: list[float] = []
    for key, value in pairwise.items():
        if not isinstance(value, dict):
            continue
        if "-" not in key:
            continue
        first, second = key.split("-", 1)
        if first in labels and second in labels:
            pairs.append((first, second))
            pvalues.append(float(value["p_value"]))
    if not pairs:
        return

    annotator = Annotator(
        ax, pairs, data=data, x=group, y=y, order=labels
    )
    annotator.configure(
        test=None,
        text_format="star",
        loc="outside",
        verbose=False,
    )
    annotator.set_pvalues_and_annotate(pvalues)


def render_scatter(
    ax: plt.Axes, data: pd.DataFrame, x: str, y: str
) -> None:
    sns.regplot(
        data=data,
        x=x,
        y=y,
        ci=95,
        seed=42,
        scatter_kws={"s": 18, "alpha": 0.7},
        line_kws={"linewidth": 1.4},
        ax=ax,
    )
    ax.set_xlabel(x)
    ax.set_ylabel(y)


def render_boxplot(
    ax: plt.Axes,
    data: pd.DataFrame,
    group: str,
    y: str,
    analysis_result: AnalysisResult | None = None,
) -> None:
    labels = [str(value) for value in sorted(pd.unique(data[group]))]
    sns.boxplot(
        data=data,
        x=group,
        y=y,
        order=labels,
        width=0.5,
        ax=ax,
        color="white",
        linewidth=1.2,
    )
    sns.stripplot(
        data=data,
        x=group,
        y=y,
        order=labels,
        size=3.2,
        alpha=0.7,
        ax=ax,
    )
    _pairwise_annotations(ax, data, group, y, analysis_result)
    ax.set_xlabel(group)
    ax.set_ylabel(y)


def render_violin(
    ax: plt.Axes,
    data: pd.DataFrame,
    group: str,
    y: str,
    analysis_result: AnalysisResult | None = None,
) -> None:
    labels = [str(value) for value in sorted(pd.unique(data[group]))]
    sns.violinplot(
        data=data,
        x=group,
        y=y,
        order=labels,
        inner=None,
        cut=0,
        ax=ax,
        linewidth=1.0,
    )
    sns.pointplot(
        data=data,
        x=group,
        y=y,
        order=labels,
        errorbar=("ci", 95),
        capsize=0.2,
        color="black",
        markersize=6,
        ax=ax,
    )
    _pairwise_annotations(ax, data, group, y, analysis_result)
    ax.set_xlabel(group)
    ax.set_ylabel(y)


def render_survival(
    ax: plt.Axes, data: pd.DataFrame, time: str, survival: str
) -> None:
    ax.step(
        data[time],
        data[survival],
        where="post",
        linewidth=1.6,
        color="#c44e52",
    )
    ax.set_ylim(0, 1.05)
    ax.set_xlabel(time)
    ax.set_ylabel("Survival probability")


def render_figure_panel(
    ax: plt.Axes,
    kind: str,
    data: pd.DataFrame,
    x: str | None,
    y: str | None,
    group: str | None,
    time: str | None,
    survival: str | None,
    analysis_result: AnalysisResult | None,
) -> None:
    if kind == "scatter":
        if x is None or y is None:
            raise ValueError("Scatter figure requires x and y columns")
        render_scatter(ax, data, x, y)
    elif kind == "boxplot":
        if group is None or y is None:
            raise ValueError("Boxplot figure requires group and y columns")
        render_boxplot(ax, data, group, y, analysis_result)
    elif kind == "violin":
        if group is None or y is None:
            raise ValueError("Violin figure requires group and y columns")
        render_violin(ax, data, group, y, analysis_result)
    elif kind == "survival":
        if time is None or survival is None:
            raise ValueError("Survival figure requires time and survival columns")
        render_survival(ax, data, time, survival)
    else:
        raise ValueError(f"Unsupported figure kind: {kind}")
