import json

import pandas as pd

from researchstat.audit import (
    AuditWriter,
    DuplicateAnalysisRecordError,
    canonical_dataset_hash,
    create_analysis_record,
)
from researchstat.engine import AnalysisRequest, run_analysis
from researchstat.planner import StatisticalPlanner
from researchstat.review import ReviewAction, review_plan


def test_canonical_dataset_hash_is_deterministic():
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0]})

    assert canonical_dataset_hash(data) == canonical_dataset_hash(data.copy())


def test_dataset_hash_changes_with_data():
    first = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    second = pd.DataFrame({"value": [1.0, 2.0, 4.0]})

    assert canonical_dataset_hash(first) != canonical_dataset_hash(second)


def test_create_analysis_record_has_required_fields():
    data = pd.DataFrame(
        {"group": ["A", "A", "B", "B"], "value": [1.0, 2.0, 3.0, 4.0]}
    )
    request = AnalysisRequest(
        protocol_id="independent_t_test_student_v1",
        data=data,
        outcome="value",
        group="group",
    )
    result = run_analysis(request)
    record = create_analysis_record(
        request=request,
        result=result,
        user_input="compare value between groups",
        analysis_id="fixed-analysis-id",
    )

    assert record.analysis_id == "fixed-analysis-id"
    assert record.protocol_id == request.protocol_id
    assert record.dataset_hash == canonical_dataset_hash(data)
    assert record.results["method"] == "independent_t_test"


def test_audit_writer_persists_and_rejects_duplicate(tmp_path):
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    request = AnalysisRequest(
        protocol_id="descriptive_v1", data=data, outcome="value"
    )
    result = run_analysis(request)
    record = create_analysis_record(
        request=request,
        result=result,
        user_input="describe value",
        analysis_id="audit-1",
    )
    writer = AuditWriter(tmp_path)

    path = writer.write(record)
    assert path.exists()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["analysis_id"] == "audit-1"

    with __import__("pytest").raises(DuplicateAnalysisRecordError):
        writer.write(record)


def test_audit_record_includes_plan_and_review():
    data = pd.DataFrame(
        {"group": ["A", "A", "B", "B"], "value": [1.0, 2.0, 3.0, 4.0]}
    )
    request = AnalysisRequest(
        protocol_id="independent_t_test_student_v1",
        data=data,
        outcome="value",
        group="group",
    )
    result = run_analysis(request)
    plan = StatisticalPlanner().plan(
        "compare value between two groups",
        data=data,
        outcome="value",
        group="group",
    )
    review = review_plan(plan, ReviewAction.ACCEPT)
    record = create_analysis_record(
        request=request,
        result=result,
        user_input="compare value between two groups",
        analysis_id="audit-review-1",
        plan=plan,
        human_review=review,
    )

    assert record.plan.recommended_protocol_id == request.protocol_id
    assert record.human_review.final_protocol_id == request.protocol_id
