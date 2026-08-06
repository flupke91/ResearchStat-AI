import json

from researchstat.figures import FigureSpec, render_figure, render_prototype_figure


def test_prototype_figure_outputs_all_formats(tmp_path):
    paths = render_prototype_figure(tmp_path)

    for key in ("svg", "pdf", "tiff", "spec"):
        assert paths[key].exists()
        assert paths[key].stat().st_size > 0


def test_svg_preserves_editable_text(tmp_path):
    paths = render_prototype_figure(tmp_path)
    svg_text = paths["svg"].read_text(encoding="utf-8")

    assert "<text" in svg_text


def test_figure_spec_is_json(tmp_path):
    paths = render_prototype_figure(tmp_path)
    spec = json.loads(paths["spec"].read_text(encoding="utf-8"))

    assert spec["svg_fonttype"] == "none"
    assert spec["renderer"].startswith("matplotlib")


def test_figure_engine_entry_point(tmp_path):
    paths = render_figure(FigureSpec(style="prototype", output_dir=tmp_path))

    assert paths["svg"].exists()
