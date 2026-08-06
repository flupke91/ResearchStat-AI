import hashlib
from pathlib import Path

import pandas as pd

from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure


GOLDEN_DIR = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "figures"
)


def test_golden_scatter_svg_hash(tmp_path):
    data = pd.DataFrame(
        {
            "x": [0.1, 0.3, 0.5, 0.7, 0.9],
            "y": [1.2, 2.0, 3.1, 4.0, 4.8],
        }
    )
    output_dir = tmp_path
    render_analysis_figure(
        FigureRequest(kind=FigureKind.SCATTER, data=data, x="x", y="y"),
        output_dir,
    )
    svg_hash = hashlib.sha256(
        (output_dir / "scatter_figure.svg").read_bytes()
    ).hexdigest()
    baseline = (GOLDEN_DIR / "golden_scatter.sha256").read_text(
        encoding="utf-8"
    ).strip()

    assert svg_hash == baseline
