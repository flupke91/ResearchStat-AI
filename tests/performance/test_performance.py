import time

import numpy as np
import pandas as pd

from researchstat.engine import AnalysisRequest, run_analysis


def test_10000_row_anova_under_10_seconds():
    rng = np.random.default_rng(7)
    data = pd.DataFrame(
        {
            "group": ["A", "B", "C"] * 3334,
            "value": rng.normal(size=10002),
        }
    ).head(10000)
    request = AnalysisRequest(
        protocol_id="one_way_anova_tukey_v1",
        data=data,
        outcome="value",
        group="group",
    )

    start = time.perf_counter()
    result = run_analysis(request)
    elapsed = time.perf_counter() - start

    assert result.statistics["n_total"] == 10000
    assert elapsed < 10, f"10000-row analysis took {elapsed:.3f}s"
