"""End-to-end demo for the Python engine and figure prototype."""

from pathlib import Path

import pandas as pd

from researchstat.engine import AnalysisRequest, run_analysis
from researchstat.figures import render_prototype_figure


def main() -> None:
    data = pd.DataFrame(
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
    result = run_analysis(
        AnalysisRequest(
            protocol_id="one_way_anova_tukey_v1",
            data=data,
            outcome="value",
            group="group",
        )
    )
    print(result.model_dump_json(indent=2))

    figure_paths = render_prototype_figure(Path(__file__).parent / "figures")
    print("\nGenerated figures:")
    for path in figure_paths.values():
        print(path)


if __name__ == "__main__":
    main()
