from pathlib import Path

import pandas as pd
import pytest

from researchstat.privacy import (
    PrivacyError,
    TemporaryWorkspace,
    mask_columns,
    mask_identifiers,
    temporary_workspace,
)


def test_mask_columns_redacts_sensitive_values():
    data = pd.DataFrame(
        {"patient_id": ["P1", "P2"], "value": [1.0, 2.0]}
    )

    masked = mask_columns(data, ["patient_id"])

    assert masked["patient_id"].tolist() == ["[REDACTED]", "[REDACTED]"]
    assert masked["value"].tolist() == [1.0, 2.0]


def test_mask_columns_rejects_missing_column():
    data = pd.DataFrame({"value": [1.0]})

    with pytest.raises(PrivacyError):
        mask_columns(data, ["patient_id"])


def test_mask_identifiers_preserves_equivalence():
    data = pd.DataFrame({"subject": ["A", "B", "A"], "value": [1.0, 2.0, 3.0]})

    masked = mask_identifiers(data, ["subject"], salt="s1")

    assert masked["subject"].iloc[0] == masked["subject"].iloc[2]
    assert masked["subject"].iloc[0] != masked["subject"].iloc[1]
    assert "A" not in masked["subject"].tolist()


def test_temporary_workspace_cleans_up():
    with temporary_workspace(prefix="researchstat-test-") as path:
        marker = Path(path) / "temp.csv"
        marker.write_text("x\n1\n", encoding="utf-8")
        assert marker.exists()
        captured = Path(path)

    assert not captured.exists()


def test_temporary_workspace_class_context(tmp_path):
    with TemporaryWorkspace(prefix="researchstat-class-") as path:
        assert Path(path).is_dir()
        captured = Path(path)

    assert not captured.exists()
