"""V1 performance benchmark: 10000 rows under 10 seconds."""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from researchstat.engine import AnalysisRequest, run_analysis


def main() -> None:
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {
            "group": ["A", "B", "C"] * 3334,
            "value": rng.normal(size=10002),
        }
    )
    data = data.head(10000)
    request = AnalysisRequest(
        protocol_id="one_way_anova_tukey_v1",
        data=data,
        outcome="value",
        group="group",
    )

    start = time.perf_counter()
    result = run_analysis(request)
    elapsed = time.perf_counter() - start

    print(f"n={len(data)} elapsed={elapsed:.4f}s F={result.statistics['F']:.4f}")
    if elapsed >= 10:
        raise SystemExit("Performance target not met: >=10 seconds")


if __name__ == "__main__":
    main()
