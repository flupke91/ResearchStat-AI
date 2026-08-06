"""Figure engine entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401
from pydantic import BaseModel

from .models import FigureRequest
from .prototype import render_prototype_figure
from .renderers import render_figure_panel


class FigureSpec(BaseModel):
    style: Literal["prototype"] = "prototype"
    output_dir: str | Path


class UnsupportedFigureStyleError(ValueError):
    """Raised when a figure spec requests an unknown renderer."""


def render_analysis_figure(
    request: FigureRequest, output_dir: str | Path
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    plt.style.use(["science", "no-latex"])
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.size"] = 9
    plt.rcParams["svg.hashsalt"] = "researchstat-v1"
    np.random.seed(42)

    fig, ax = plt.subplots(figsize=(request.width, request.height))
    render_figure_panel(
        ax=ax,
        kind=request.kind.value,
        data=request.data,
        x=request.x,
        y=request.y,
        group=request.group,
        time=request.time,
        survival=request.survival,
        analysis_result=request.analysis_result,
    )
    fig.tight_layout()

    base_name = f"{request.kind.value}_figure"
    svg_path = output / f"{base_name}.svg"
    pdf_path = output / f"{base_name}.pdf"
    tiff_path = output / f"{base_name}.tiff"
    fig.savefig(
        svg_path,
        format="svg",
        metadata={"Date": "2026-01-01T00:00:00"},
    )
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(tiff_path, format="tiff", dpi=request.dpi)
    plt.close(fig)

    spec = {
        "kind": request.kind.value,
        "analysis_id": request.analysis_id,
        "x": request.x,
        "y": request.y,
        "group": request.group,
        "time": request.time,
        "survival": request.survival,
        "analysis_result": (
            request.analysis_result.model_dump()
            if request.analysis_result is not None
            else None
        ),
        "renderer": "matplotlib+seaborn+statannotations",
        "svg_fonttype": "none",
        "tiff_dpi": request.dpi,
    }
    spec_path = output / f"{base_name}_spec.json"
    spec_path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "svg": svg_path,
        "pdf": pdf_path,
        "tiff": tiff_path,
        "spec": spec_path,
    }


def render_figure(
    request: FigureSpec | FigureRequest | dict,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    if isinstance(request, FigureRequest):
        if output_dir is None:
            raise TypeError("FigureRequest rendering requires output_dir")
        return render_analysis_figure(request, output_dir)
    if isinstance(request, FigureSpec):
        return render_prototype_figure(request.output_dir)
    parsed = FigureSpec.model_validate(request)
    return render_prototype_figure(parsed.output_dir)
