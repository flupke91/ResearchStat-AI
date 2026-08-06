"""Cross-engine numerical validation between Python and R."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..engine import AnalysisRequest, AnalysisResult, run_analysis, run_r_analysis
from ..protocols.registry import ProtocolRegistry


class ComparisonKind(str, Enum):
    CONTINUOUS = "continuous"
    PVALUE = "p_value"


@dataclass(frozen=True)
class Comparison:
    path: str
    python_value: float | None
    r_value: float | None
    kind: ComparisonKind
    passed: bool
    detail: str = ""


@dataclass
class CrossEngineReport:
    protocol_id: str
    method: str
    python_result: AnalysisResult
    r_result: AnalysisResult
    comparisons: list[Comparison] = field(default_factory=list)
    passed: bool = False

    @property
    def failed_comparisons(self) -> list[Comparison]:
        return [item for item in self.comparisons if not item.passed]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _values_equal(
    python_value: float, r_value: float, kind: ComparisonKind
) -> tuple[bool, str]:
    if math.isnan(python_value) and math.isnan(r_value):
        return True, "both NaN"
    if math.isnan(python_value) or math.isnan(r_value):
        return False, "one side is NaN"

    if kind is ComparisonKind.PVALUE:
        absolute = abs(python_value - r_value)
        if absolute <= 1e-6:
            return True, f"absolute difference {absolute:.3e}"
        if min(python_value, r_value) < 1e-8:
            relative = absolute / max(abs(python_value), abs(r_value), 1e-300)
            if relative <= 1e-6:
                return True, f"relative difference {relative:.3e}"
        return False, f"absolute difference {absolute:.3e} > 1e-6"

    if python_value == 0 and r_value == 0:
        return True, "both zero"
    if abs(python_value) <= 1e-12 and abs(r_value) <= 1e-12:
        return True, "both near zero"
    scale = max(abs(python_value), abs(r_value), 1e-300)
    relative = abs(python_value - r_value) / scale
    if relative <= 1e-8:
        return True, f"relative difference {relative:.3e}"
    return False, f"relative difference {relative:.3e} > 1e-8"


def _compare_mapping(
    prefix: str,
    python_mapping: dict[str, Any],
    r_mapping: dict[str, Any],
    kind: ComparisonKind,
    comparisons: list[Comparison],
) -> None:
    for key in sorted(python_mapping.keys() | r_mapping.keys()):
        path = f"{prefix}.{key}" if prefix else key
        python_value = python_mapping.get(key)
        r_value = r_mapping.get(key)

        if (key not in python_mapping) or (key not in r_mapping):
            if _is_number(python_value) or _is_number(r_value):
                comparisons.append(
                    Comparison(
                        path=path,
                        python_value=(
                            float(python_value) if _is_number(python_value) else None
                        ),
                        r_value=(
                            float(r_value) if _is_number(r_value) else None
                        ),
                        kind=kind,
                        passed=False,
                        detail="numeric value missing on one side",
                    )
                )
            continue

        if isinstance(python_value, dict) or isinstance(r_value, dict):
            _compare_mapping(
                path,
                python_value if isinstance(python_value, dict) else {},
                r_value if isinstance(r_value, dict) else {},
                kind,
                comparisons,
            )
            continue

        if isinstance(python_value, list) or isinstance(r_value, list):
            _compare_list(
                path,
                python_value if isinstance(python_value, list) else [],
                r_value if isinstance(r_value, list) else [],
                kind,
                comparisons,
            )
            continue

        if _is_number(python_value) and _is_number(r_value):
            passed, detail = _values_equal(
                float(python_value), float(r_value), kind
            )
            comparisons.append(
                Comparison(
                    path=path,
                    python_value=float(python_value),
                    r_value=float(r_value),
                    kind=kind,
                    passed=passed,
                    detail=detail,
                )
            )


def _compare_list(
    prefix: str,
    python_values: list[Any],
    r_values: list[Any],
    kind: ComparisonKind,
    comparisons: list[Comparison],
) -> None:
    for index in range(max(len(python_values), len(r_values))):
        path = f"{prefix}[{index}]"
        python_value = python_values[index] if index < len(python_values) else None
        r_value = r_values[index] if index < len(r_values) else None

        if isinstance(python_value, dict) or isinstance(r_value, dict):
            _compare_mapping(
                path,
                python_value if isinstance(python_value, dict) else {},
                r_value if isinstance(r_value, dict) else {},
                kind,
                comparisons,
            )
            continue
        if _is_number(python_value) and _is_number(r_value):
            passed, detail = _values_equal(
                float(python_value), float(r_value), kind
            )
            comparisons.append(
                Comparison(
                    path=path,
                    python_value=float(python_value),
                    r_value=float(r_value),
                    kind=kind,
                    passed=passed,
                    detail=detail,
                )
            )


def cross_validate(
    request: AnalysisRequest,
    registry: ProtocolRegistry | None = None,
) -> CrossEngineReport:
    registry = registry or ProtocolRegistry.load_default()
    python_result = run_analysis(request, registry=registry)
    r_result = run_r_analysis(request, registry=registry)

    comparisons: list[Comparison] = []
    _compare_mapping(
        "statistics",
        python_result.statistics,
        r_result.statistics,
        ComparisonKind.CONTINUOUS,
        comparisons,
    )
    _compare_mapping(
        "p_values",
        python_result.p_values,
        r_result.p_values,
        ComparisonKind.PVALUE,
        comparisons,
    )
    _compare_mapping(
        "effect_size",
        python_result.effect_size,
        r_result.effect_size,
        ComparisonKind.CONTINUOUS,
        comparisons,
    )

    return CrossEngineReport(
        protocol_id=request.protocol_id,
        method=python_result.method,
        python_result=python_result,
        r_result=r_result,
        comparisons=comparisons,
        passed=all(item.passed for item in comparisons),
    )
