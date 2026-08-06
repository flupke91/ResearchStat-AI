import pytest

from researchstat.protocols.registry import (
    DuplicateProtocolError,
    ProtocolNotFoundError,
    ProtocolRegistry,
)


EXPECTED_V1_IDS = {
    "descriptive_v1",
    "independent_t_test_student_v1",
    "independent_t_test_welch_v1",
    "paired_t_test_v1",
    "one_way_anova_tukey_v1",
    "two_way_anova_v1",
    "mann_whitney_u_v1",
    "kruskal_wallis_dunn_v1",
    "pearson_correlation_v1",
    "spearman_correlation_v1",
    "linear_regression_v1",
}


def test_default_registry_contains_all_v1_protocols():
    registry = ProtocolRegistry.load_default()

    assert set(registry.ids()) == EXPECTED_V1_IDS


def test_load_yaml_from_file(tmp_path):
    path = tmp_path / "protocols.yaml"
    path.write_text(
        "protocols:\n"
        "  - id: custom_protocol_v1\n"
        "    version: 1\n"
        "    method: descriptive\n"
        "    assumptions:\n"
        "      observations_independent: true\n"
        "      normality_checked: false\n"
        "      variance: not_applicable\n"
        "    posthoc: none\n"
        "    alpha: 0.05\n"
        "    missing_policy: complete_case\n"
        "    effect_size: none\n",
        encoding="utf-8",
    )

    registry = ProtocolRegistry.load_yaml(path)

    assert registry.get("custom_protocol_v1").method.value == "descriptive"


def test_duplicate_protocol_id_is_rejected():
    registry = ProtocolRegistry()
    payload = {
        "id": "duplicate_v1",
        "version": 1,
        "method": "descriptive",
        "assumptions": {
            "observations_independent": True,
            "normality_checked": False,
            "variance": "not_applicable",
        },
        "posthoc": "none",
        "alpha": 0.05,
        "missing_policy": "complete_case",
        "effect_size": "none",
    }

    registry.register(payload)

    with pytest.raises(DuplicateProtocolError):
        registry.register(payload)


def test_get_missing_protocol_raises():
    registry = ProtocolRegistry.load_default()

    with pytest.raises(ProtocolNotFoundError):
        registry.get("does_not_exist_v1")


def test_search_by_method():
    registry = ProtocolRegistry.load_default()

    matches = registry.search(method="independent_t_test")

    assert {p.id for p in matches} == {
        "independent_t_test_student_v1",
        "independent_t_test_welch_v1",
    }


def test_search_by_posthoc_and_variance():
    registry = ProtocolRegistry.load_default()

    matches = registry.search(
        method="one_way_anova",
        posthoc="tukey_hsd",
        variance="equal_variance",
    )

    assert [p.id for p in matches] == ["one_way_anova_tukey_v1"]


def test_search_is_stable_and_sorted():
    registry = ProtocolRegistry.load_default()

    assert registry.ids() == sorted(registry.ids())
