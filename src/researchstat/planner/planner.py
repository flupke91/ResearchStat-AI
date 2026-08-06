"""Offline rule-based statistical planner.

V1 defaults to a deterministic offline planner. External LLM backends may be
added later, but every recommendation must still resolve to a Protocol Registry
id and pass through the human review gate.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from ..protocols.registry import ProtocolRegistry
from ..protocols.schema import StatisticalMethod
from .models import GroupStructure, StatisticalPlan, VariableType


_GROUP_COUNT_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


class StatisticalPlanner:
    def __init__(
        self, registry: ProtocolRegistry | None = None
    ) -> None:
        self.registry = registry or ProtocolRegistry.load_default()

    def plan(
        self,
        user_input: str,
        data: pd.DataFrame | None = None,
        outcome: str | None = None,
        group: str | None = None,
        factor2: str | None = None,
        paired_by: str | None = None,
        predictors: tuple[str, ...] = (),
    ) -> StatisticalPlan:
        text = user_input.lower()
        inference = self._infer_data(
            text, data, outcome, group, factor2, paired_by, predictors
        )
        outcome_name = inference["outcome"]
        group_name = inference["group"]
        factor2_name = inference["factor2"]
        paired_by_name = inference["paired_by"]
        groups = inference["groups"]

        intent = self._detect_intent(text)
        paired_hint = has_any(text, _PAIRED_HINTS)
        nonnormal_hint = has_any(text, _NONNORMAL_HINTS)
        unequal_variance_hint = has_any(text, _UNEQUAL_VARIANCE_HINTS)
        structure = (
            GroupStructure.PAIRED
            if paired_hint or paired_by_name is not None
            else GroupStructure.INDEPENDENT
            if groups and groups > 1
            else GroupStructure.UNKNOWN
        )

        if intent == "survival":
            return self._needs_more_info(
                "Survival analysis is planned for V1.5, not V1."
            )

        if intent == "correlation":
            protocol_id = (
                "spearman_correlation_v1"
                if nonnormal_hint
                else "pearson_correlation_v1"
            )
            return self._ready_plan(
                user_input=user_input,
                experiment_type="Association study",
                variable_type=VariableType.CONTINUOUS,
                groups=2,
                structure=GroupStructure.INDEPENDENT,
                protocol_id=protocol_id,
                reason=(
                    f"Intent is correlation between {outcome_name or 'outcome'} "
                    f"and a predictor variable."
                ),
                confidence=0.8 if outcome_name else 0.5,
            )

        if intent == "regression":
            return self._ready_plan(
                user_input=user_input,
                experiment_type="Regression study",
                variable_type=VariableType.CONTINUOUS,
                groups=None,
                structure=structure,
                protocol_id="linear_regression_v1",
                reason=(
                    f"Intent is regression with outcome {outcome_name or 'outcome'} "
                    f"and predictors {', '.join(predictors) or 'to be specified'}."
                ),
                confidence=0.8 if outcome_name else 0.5,
            )

        if intent == "compare":
            if groups is None:
                return self._needs_more_info(
                    "Comparison intent detected but group count is unknown."
                )
            if factor2_name is not None:
                protocol_id = "two_way_anova_v1"
            elif groups == 2:
                if paired_hint:
                    protocol_id = "paired_t_test_v1"
                elif nonnormal_hint:
                    protocol_id = "mann_whitney_u_v1"
                elif unequal_variance_hint:
                    protocol_id = "independent_t_test_welch_v1"
                else:
                    protocol_id = "independent_t_test_student_v1"
            elif groups >= 3:
                if nonnormal_hint:
                    protocol_id = "kruskal_wallis_dunn_v1"
                else:
                    protocol_id = "one_way_anova_tukey_v1"
            else:
                return self._needs_more_info(
                    "Comparison requires at least 2 groups."
                )

            return self._ready_plan(
                user_input=user_input,
                experiment_type=self._experiment_type(text),
                variable_type=VariableType.CONTINUOUS,
                groups=groups,
                structure=structure,
                protocol_id=protocol_id,
                reason=(
                    f"Comparison intent across {groups} group(s); "
                    f"outcome is continuous; structure is {structure.value}; "
                    "protocol assumption checks will be run before execution."
                ),
                confidence=0.8 if group_name else 0.5,
            )

        if factor2_name is not None and outcome_name is not None:
            return self._ready_plan(
                user_input=user_input,
                experiment_type="Two-factor comparative study",
                variable_type=VariableType.CONTINUOUS,
                groups=groups,
                structure=GroupStructure.INDEPENDENT,
                protocol_id="two_way_anova_v1",
                reason=(
                    f"Data contains two categorical factors: "
                    f"{group_name or 'factor1'} and {factor2_name}."
                ),
                confidence=0.7,
            )

        if outcome_name is not None:
            return self._ready_plan(
                user_input=user_input,
                experiment_type="Descriptive study",
                variable_type=VariableType.CONTINUOUS,
                groups=groups,
                structure=structure,
                protocol_id="descriptive_v1",
                reason="No comparison, correlation, or regression intent detected.",
                confidence=0.6,
            )

        return self._needs_more_info(
            "Please provide data columns or a clearer analysis question."
        )

    def _ready_plan(
        self,
        user_input: str,
        experiment_type: str,
        variable_type: VariableType,
        groups: int | None,
        structure: GroupStructure,
        protocol_id: str,
        reason: str,
        confidence: float,
    ) -> StatisticalPlan:
        protocol = self.registry.get(protocol_id)
        assumptions = self._assumptions_for(protocol)
        alternatives = [
            candidate.id
            for candidate in self.registry.search(method=protocol.method)
            if candidate.id != protocol_id
        ]
        return StatisticalPlan(
            status="ready",
            experiment_type=experiment_type,
            variable_type=variable_type,
            groups=groups,
            group_structure=structure,
            recommended_protocol_id=protocol_id,
            reason=reason,
            assumptions_to_check=assumptions,
            alternatives=alternatives,
            confidence=confidence,
        )

    def _needs_more_info(self, reason: str) -> StatisticalPlan:
        return StatisticalPlan(
            status="needs_more_info",
            experiment_type="unknown",
            variable_type=VariableType.UNKNOWN,
            groups=None,
            group_structure=GroupStructure.UNKNOWN,
            recommended_protocol_id=None,
            reason=reason,
            assumptions_to_check=[],
            alternatives=[],
            confidence=0.0,
        )

    @staticmethod
    def _assumptions_for(protocol) -> list[str]:
        checks = ["observations_independent", "sample_size"]
        if protocol.assumptions.normality_checked:
            checks.append("shapiro_wilk")
        if protocol.assumptions.variance.value != "not_applicable":
            checks.append("levene_equal_variance")
        return checks

    @staticmethod
    def _detect_intent(text: str) -> str:
        if has_any(text, _SURVIVAL_HINTS):
            return "survival"
        if has_any(text, _CORRELATION_HINTS):
            return "correlation"
        if has_any(text, _REGRESSION_HINTS):
            return "regression"
        if has_any(text, _COMPARE_HINTS):
            return "compare"
        return "unknown"

    @staticmethod
    def _experiment_type(text: str) -> str:
        if has_any(text, ("animal", "mouse", "rat", "tumor")):
            return "Animal study"
        if has_any(text, ("patient", "clinical", "trial", "drug")):
            return "Clinical study"
        return "Comparative study"

    def _infer_data(
        self,
        text: str,
        data: pd.DataFrame | None,
        outcome: str | None,
        group: str | None,
        factor2: str | None,
        paired_by: str | None,
        predictors: tuple[str, ...],
    ) -> dict[str, Any]:
        if data is None:
            return {
                "outcome": outcome,
                "group": group,
                "factor2": factor2,
                "paired_by": paired_by,
                "groups": self._text_group_count(text),
            }

        numeric_columns = [
            column
            for column in data.columns
            if pd.api.types.is_numeric_dtype(data[column])
        ]
        if outcome is None:
            outcome = next(
                (
                    column
                    for column in numeric_columns
                    if has_any(column.lower(), _OUTCOME_HINTS)
                ),
                numeric_columns[0] if numeric_columns else None,
            )

        categorical_columns = [
            column
            for column in data.columns
            if not pd.api.types.is_numeric_dtype(data[column])
            and data[column].nunique(dropna=True) <= 10
        ]
        if group is None:
            group = next(
                (
                    column
                    for column in categorical_columns
                    if has_any(column.lower(), _GROUP_HINTS)
                ),
                categorical_columns[0] if categorical_columns else None,
            )
        if factor2 is None:
            factor2 = next(
                (
                    column
                    for column in categorical_columns
                    if column != group
                    and has_any(column.lower(), _FACTOR2_HINTS)
                ),
                None,
            )

        id_columns = [
            column
            for column in data.columns
            if data[column].nunique(dropna=True) > 10
            and has_any(column.lower(), _ID_HINTS)
        ]
        if paired_by is None:
            paired_by = id_columns[0] if id_columns else None

        groups = None
        if group is not None:
            groups = int(data[group].nunique(dropna=True))
        return {
            "outcome": outcome,
            "group": group,
            "factor2": factor2,
            "paired_by": paired_by,
            "groups": groups,
        }

    def _text_group_count(self, text: str) -> int | None:
        for word, count in _GROUP_COUNT_WORDS.items():
            if (
                f"{word} group" in text
                or f"{word} treatment" in text
                or f"{word} drug" in text
                or f"{word} arm" in text
            ):
                return count
        numbers = re.findall(r"\b([2-9]|10)\b", text)
        if numbers and any(
            word in text for word in ("group", "treatment", "drug", "arm")
        ):
            return int(numbers[0])
        return None


_COMPARE_HINTS = (
    "compare",
    "between",
    "different",
    "difference",
    "effect",
    "versus",
    " vs ",
    "among",
    "across",
    "treatment",
)
_CORRELATION_HINTS = (
    "correlat",
    "association",
    "relationship",
    "related",
    "association between",
)
_REGRESSION_HINTS = ("regress", "predict", "prediction", "dose-response", "slope")
_SURVIVAL_HINTS = ("survival", "kaplan", "time-to-event", "censored")
_PAIRED_HINTS = (
    "paired",
    "pre-post",
    "pre post",
    "before-after",
    "before after",
    "within",
    "matched",
    "repeated",
    "longitudinal",
)
_NONNORMAL_HINTS = ("non-normal", "nonnormal", "skewed", "rank", "nonparametric")
_UNEQUAL_VARIANCE_HINTS = ("unequal", "welch", "not equal variance")
_OUTCOME_HINTS = ("outcome", "score", "value", "y", "response", "measure")
_GROUP_HINTS = ("group", "treatment", "condition", "arm", "dose", "type", "species")
_FACTOR2_HINTS = ("factor2", "factor_2", "sex", "gender", "time", "block")
_ID_HINTS = ("id", "subject", "patient", "mouse", "rat")


def has_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)
