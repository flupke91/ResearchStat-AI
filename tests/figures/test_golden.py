import json
import re
from pathlib import Path

import pandas as pd

from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure


GOLDEN_DIR = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "figures"
)


def _svg_structure(text: str) -> dict[str, int | str]:
    return {
        "text_count": len(re.findall(r"<text", text)),
        "path_count": len(re.findall(r"<path", text)),
        "use_count": len(re.findall(r"<use", text)),
        "metadata_date": re.search(r"<dc:date>([^<]+)", text).group(1),
    }


def test_golden_scatter_svg_structure(tmp_path):
    data = pd.DataFrame(
        {
            "x": [0.1, 0.3, 0.5, 0.7, 0.9],
            "y": [1.2, 2.0, 3.1, 4.0, 4.8],
        }
    )
    render_analysis_figure(
        FigureRequest(kind=FigureKind.SCATTER, data=data, x="x", y="y"),
        tmp_path,
    )
    svg_text = (tmp_path / "scatter_figure.svg").read_text(encoding="utf-8")
    baseline = json.loads(
        (GOLDEN_DIR / "golden_scatter.json").read_text(encoding="utf-8")
    )

    assert _svg_structure(svg_text) == baseline
