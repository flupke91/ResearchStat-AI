import json

import pandas as pd
import pytest

from researchstat.workflow import WorkflowError, run_analysis_workflow


def test_full_workflow_writes_audit_record(tmp_path):
    data = pd.DataFrame(
        {"group": ["A", "A", "A", "B", "B", "B"], "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}
    )
    output = run_analysis_workflow(
        user_input="compare value between two groups",
        data=data,
        outcome="value",
        group="group",
        audit_dir=tmp_path,
    )

    assert output["plan"].recommended_protocol_id == "independent_t_test_student_v1"
    assert output["review"].final_protocol_id == "independent_t_test_student_v1"
    assert output["result"].protocol_id == "independent_t_test_student_v1"
    assert output["record_path"].exists()
    saved = json.loads(output["record_path"].read_text(encoding="utf-8"))
    assert saved["user_input"] == "compare value between two groups"
    assert saved["human_review"]["action"] == "accept"


def test_workflow_override_records_review(tmp_path):
    data = pd.DataFrame(
        {"group": ["A", "A", "A", "B", "B", "B"], "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}
    )
    output = run_analysis_workflow(
        user_input="compare value between two groups",
        data=data,
        outcome="value",
        group="group",
        review_action="override",
        override_protocol_id="independent_t_test_welch_v1",
        review_reason="unequal variance expected",
        audit_dir=tmp_path,
    )

    assert output["result"].protocol_id == "independent_t_test_welch_v1"
    assert output["record"].human_review.reason == "unequal variance expected"


def test_workflow_requires_more_info_for_survival():
    data = pd.DataFrame({"time": [1.0, 2.0, 3.0], "event": [1, 0, 1]})

    with pytest.raises(WorkflowError):
        run_analysis_workflow(
            user_input="survival analysis of time to event",
            data=data,
        )


def test_workflow_masks_identifiers_before_audit(tmp_path):
    data = pd.DataFrame(
        {
            "subject": ["S1", "S2", "S3", "S4", "S5", "S6"],
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )
    output = run_analysis_workflow(
        user_input="compare value between two groups",
        data=data,
        outcome="value",
        group="group",
        identifier_columns=("subject",),
        identifier_salt="test",
        audit_dir=tmp_path,
    )

    assert "S1" not in output["record"].results["metadata"].get("groups", [])
    saved = json.loads(output["record_path"].read_text(encoding="utf-8"))
    assert "S1" not in json.dumps(saved)
