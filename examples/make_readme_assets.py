"""Generate reproducible figures and audit examples for README docs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image

from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure
from researchstat.workflow import run_analysis_workflow


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
AUDIT_DIR = ROOT / "examples" / "audit_records"


def _analysis_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": ["ctrl"] * 12 + ["trt1"] * 12 + ["trt2"] * 12,
            "value": [
                9.2, 10.1, 9.8, 11.0, 10.4, 9.6,
                10.8, 9.4, 10.6, 11.2, 9.9, 10.3,
                11.1, 12.4, 12.0, 13.2, 12.8, 11.9,
                12.6, 13.1, 12.3, 13.8, 12.2, 13.0,
                15.1, 16.2, 15.4, 17.0, 16.5, 15.8,
                16.9, 17.2, 18.1, 16.8, 17.6, 16.4,
            ],
        }
    )


def _scatter_data() -> pd.DataFrame:
    import numpy as np

    rng = np.random.default_rng(7)
    x = rng.normal(size=40)
    y = 2.1 * x + rng.normal(0, 0.6, size=40)
    return pd.DataFrame({"x": x, "y": y})


def _png_preview(tiff_path: Path, png_path: Path) -> None:
    Image.open(tiff_path).save(png_path, dpi=(300, 300))


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    data = _analysis_data()

    workflow = run_analysis_workflow(
        user_input="compare three drugs on mouse tumor size",
        data=data,
        outcome="value",
        group="group",
        audit_dir=AUDIT_DIR,
    )

    box_paths = render_analysis_figure(
        FigureRequest(
            kind=FigureKind.BOXPLOT,
            data=data,
            group="group",
            y="value",
            analysis_result=workflow["result"],
            analysis_id=workflow["record"].analysis_id,
        ),
        IMAGE_DIR / "boxplot",
    )
    _png_preview(box_paths["tiff"], IMAGE_DIR / "boxplot_preview.png")

    scatter_data = _scatter_data()
    scatter_paths = render_analysis_figure(
        FigureRequest(
            kind=FigureKind.SCATTER,
            data=scatter_data,
            x="x",
            y="y",
        ),
        IMAGE_DIR / "scatter",
    )
    _png_preview(scatter_paths["tiff"], IMAGE_DIR / "scatter_preview.png")

    print(f"analysis_id={workflow['record'].analysis_id}")
    print(f"audit={workflow['record_path']}")
    print(f"boxplot={box_paths['svg']}")
    print(f"scatter={scatter_paths['svg']}")


if __name__ == "__main__":
    main()
