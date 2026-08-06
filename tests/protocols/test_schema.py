import pytest
from pydantic import ValidationError

from researchstat.protocols.schema import Protocol


def protocol_payload(method="descriptive", **overrides):
    payload = {
        "id": "test_protocol_v1",
        "version": 1,
        "method": method,
        "assumptions": {
            "observations_independent": True,
            "normality_checked": False,
            "variance": "not_applicable",
        },
        "posthoc": "none",
        "alpha": 0.05,
        "missing_policy": "complete_case",
        "effect_size": "none",
        "description": "",
        "parameters": {},
    }
    payload.update(overrides)
    return payload


def test_valid_one_way_anova_protocol():
    protocol = Protocol.model_validate(
        protocol_payload(
            method="one_way_anova",
            posthoc="tukey_hsd",
            effect_size="eta_squared",
            assumptions={
                "observations_independent": True,
                "normality_checked": True,
                "variance": "equal_variance",
            },
        )
    )

    assert protocol.id == "test_protocol_v1"
    assert protocol.posthoc.value == "tukey_hsd"


def test_rejects_alpha_out_of_range():
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol_payload(alpha=1.0))


def test_rejects_unknown_posthoc():
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol_payload(posthoc="bonferroni"))


def test_rejects_invalid_protocol_id():
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol_payload(id="One-Way"))


def test_rejects_anova_without_tukey():
    with pytest.raises(ValidationError):
        Protocol.model_validate(
            protocol_payload(
                method="one_way_anova",
                assumptions={
                    "observations_independent": True,
                    "normality_checked": True,
                    "variance": "equal_variance",
                },
            )
        )


def test_rejects_independent_t_without_variance_assumption():
    with pytest.raises(ValidationError):
        Protocol.model_validate(
            protocol_payload(
                method="independent_t_test",
                assumptions={
                    "observations_independent": True,
                    "normality_checked": True,
                    "variance": "not_applicable",
                },
            )
        )


def test_rejects_paired_t_with_variance_assumption():
    with pytest.raises(ValidationError):
        Protocol.model_validate(
            protocol_payload(
                method="paired_t_test",
                assumptions={
                    "observations_independent": True,
                    "normality_checked": True,
                    "variance": "equal_variance",
                },
            )
        )


def test_rejects_descriptive_with_posthoc():
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol_payload(posthoc="tukey_hsd"))
