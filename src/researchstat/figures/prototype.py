"""Prototype renderer for professional-grade publication figures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scienceplots  # noqa: F401
import seaborn as sns
from statannotations.Annotator import Annotator


def _sample_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    groups = ["ctrl", "trt1", "trt2"]
    rows = []
    for group, mean in zip(groups, [10.0, 12.5, 16.0]):
        values = rng.normal(mean, 1.4, size=24)
        for value in values:
            rows.append({"group": group, "value": value})
    return pd.DataFrame(rows)


def _survival_data() -> pd.DataFrame:
    times = np.array([0, 5, 8, 12, 18, 24, 30], dtype=float)
    survival = np.array([1.0, 0.95, 0.85, 0.75, 0.6, 0.45, 0.4])
    return pd.DataFrame({"time": times, "survival": survival})


def _figure_spec() -> dict[str, Any]:
    return {
        "title": "ResearchStat AI Figure Prototype",
        "data": "synthetic PlantGrowth-like example",
        "panels": {
            "A": "boxplot with individual points and significance annotation",
            "B": "violin plot with significance annotation",
            "C": "scatter plot with regression line and confidence band",
            "D": "survival step curve",
        },
        "style": ["science", "no-latex"],
        "renderer": "matplotlib+seaborn+statannotations",
        "svg_fonttype": "none",
        "tiff_dpi": 300,
    }


def _add_annotations(
    ax: plt.Axes,
    data: pd.DataFrame,
    pairs: list[tuple[str, str]],
    test: str = "Mann-Whitney",
) -> None:
    annotator = Annotator(
        ax,
        pairs,
        data=data,
        x="group",
        y="value",
        order=["ctrl", "trt1", "trt2"],
    )
    annotator.configure(
        test=test,
        text_format="star",
        loc="outside",
        comparisons_correction="holm-bonferroni",
        verbose=False,
    )
    annotator.apply_and_annotate()


def render_prototype_figure(output_dir: str | Path) -> dict[str, Path]:
    """Render a multi-panel prototype and return generated file paths."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    plt.style.use(["science", "no-latex"])
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.size"] = 9
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["svg.hashsalt"] = "researchstat-v1"
    np.random.seed(42)

    data = _sample_data()
    survival = _survival_data()

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
    fig.suptitle("ResearchStat AI Figure Prototype", fontsize=12)

    ax = axes[0, 0]
    sns.boxplot(
        data=data,
        x="group",
        y="value",
        order=["ctrl", "trt1", "trt2"],
        width=0.5,
        ax=ax,
        color="white",
        linewidth=1.2,
    )
    sns.stripplot(
        data=data,
        x="group",
        y="value",
        order=["ctrl", "trt1", "trt2"],
        size=3.2,
        alpha=0.7,
        ax=ax,
    )
    _add_annotations(ax, data, [("ctrl", "trt2"), ("trt1", "trt2")])
    ax.set_title("A", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlabel("")
    ax.set_ylabel("Value")

    ax = axes[0, 1]
    sns.violinplot(
        data=data,
        x="group",
        y="value",
        order=["ctrl", "trt1", "trt2"],
        inner=None,
        cut=0,
        ax=ax,
        linewidth=1.0,
    )
    sns.pointplot(
        data=data,
        x="group",
        y="value",
        order=["ctrl", "trt1", "trt2"],
        errorbar=("ci", 95),
        capsize=0.2,
        color="black",
        markersize=6,
        ax=ax,
    )
    _add_annotations(ax, data, [("ctrl", "trt1"), ("ctrl", "trt2")])
    ax.set_title("B", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlabel("")
    ax.set_ylabel("Value")

    ax = axes[1, 0]
    rng = np.random.default_rng(7)
    x = rng.normal(size=40)
    y = 2.1 * x + rng.normal(0, 0.6, size=40)
    scatter_data = pd.DataFrame({"x": x, "y": y})
    sns.regplot(
        data=scatter_data,
        x="x",
        y="y",
        ci=95,
        scatter_kws={"s": 18, "alpha": 0.7},
        line_kws={"linewidth": 1.4},
        ax=ax,
    )
    ax.set_title("C", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlabel("Predictor")
    ax.set_ylabel("Outcome")

    ax = axes[1, 1]
    ax.step(
        survival["time"],
        survival["survival"],
        where="post",
        linewidth=1.6,
        color="#c44e52",
    )
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, 30)
    ax.set_title("D", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")

    fig.tight_layout(rect=(0, 0, 1, 0.96))

    svg_path = output / "prototype_figure.svg"
    pdf_path = output / "prototype_figure.pdf"
    tiff_path = output / "prototype_figure.tiff"
    fig.savefig(
        svg_path,
        format="svg",
        metadata={"Date": "2026-01-01T00:00:00"},
    )
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(tiff_path, format="tiff", dpi=300)
    plt.close(fig)

    spec_path = output / "prototype_figure_spec.json"
    spec_path.write_text(
        json.dumps(_figure_spec(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "svg": svg_path,
        "pdf": pdf_path,
        "tiff": tiff_path,
        "spec": spec_path,
    }
