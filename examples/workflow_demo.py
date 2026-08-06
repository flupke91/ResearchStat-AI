"""Demonstrate the plan -> review -> execute -> audit workflow."""

from pathlib import Path

import pandas as pd

from researchstat.workflow import run_analysis_workflow


def main() -> None:
    data = pd.DataFrame(
        {
            "group": ["ctrl"] * 10 + ["trt1"] * 10 + ["trt2"] * 10,
            "value": [
                9.2, 10.1, 9.8, 11.0, 10.4, 9.6, 10.8, 9.4, 10.6, 11.2,
                12.1, 13.0, 12.4, 13.8, 12.2, 13.2, 12.9, 13.5, 12.6, 13.1,
                15.1, 16.2, 15.4, 17.0, 16.5, 15.8, 16.9, 17.2, 18.1, 16.8,
            ],
        }
    )
    audit_dir = Path(__file__).parent / "audit_records"
    output = run_analysis_workflow(
        user_input="compare three drugs on mouse tumor size",
        data=data,
        outcome="value",
        group="group",
        audit_dir=audit_dir,
    )
    print("Recommended protocol:", output["plan"].recommended_protocol_id)
    print("Reviewed protocol:", output["review"].final_protocol_id)
    print("Audit record:", output["record_path"])


if __name__ == "__main__":
    main()
