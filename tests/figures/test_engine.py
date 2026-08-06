import json

import pandas as pd

from researchstat.engine import AnalysisRequest, run_analysis
from researchstat.figures import FigureKind, FigureRequest, render_analysis_figure


def _boxplot_request():
    data = pd.DataFrame(
        {
            "group": ["A"] * 8 + ["B"] * 8,
            "value": [
                1.0, 2.0, 2.5, 3.0, 3.2, 4.0, 4.5, 5.0,
                4.0, 5.0, 5.5, 6.0, 6.2, 7.0, 7.5, 8.0,
            ],
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
    return FigureRequest(
        kind=FigureKind.BOXPLOT,
        data=data,
        group="group",
        y="value",
        analysis_result=result,
        analysis_id="figure-analysis-1",
    )


def test_render_analysis_boxplot_with_audit_binding(tmp_path):
    paths = render_analysis_figure(_boxplot_request(), tmp_path)

    assert paths["svg"].exists()
    assert paths["pdf"].exists()
    assert paths["tiff"].exists()
    svg_text = paths["svg"].read_text(encoding="utf-8")
    assert "<text" in svg_text

    spec = json.loads(paths["spec"].read_text(encoding="utf-8"))
    assert spec["analysis_id"] == "figure-analysis-1"
    assert spec["analysis_result"]["protocol_id"] == "independent_t_test_student_v1"


def test_render_analysis_scatter(tmp_path):
    data = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.5, 2.0, 3.5, 4.0]})
    paths = render_analysis_figure(
        FigureRequest(kind=FigureKind.SCATTER, data=data, x="x", y="y"),
        tmp_path,
    )

    assert paths["svg"].exists()
    assert paths["tiff"].stat().st_size > 0


def test_render_analysis_violin_and_survival(tmp_path):
    data = pd.DataFrame(
        {"group": ["A"] * 5 + ["B"] * 5, "value": list(range(1, 11))}
    )
    render_analysis_figure(
        FigureRequest(
            kind=FigureKind.VIOLIN,
            data=data,
            group="group",
            y="value",
        ),
        tmp_path / "violin",
    )

    survival = pd.DataFrame(
        {"time": [0.0, 5.0, 10.0, 15.0], "survival": [1.0, 0.8, 0.6, 0.4]}
    )
    render_analysis_figure(
        FigureRequest(
            kind=FigureKind.SURVIVAL,
            data=survival,
            time="time",
            survival="survival",
        ),
        tmp_path / "survival",
    )

    assert (tmp_path / "violin" / "violin_figure.svg").exists()
    assert (tmp_path / "survival" / "survival_figure.svg").exists()
