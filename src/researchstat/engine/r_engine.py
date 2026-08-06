"""R subprocess adapter for the statistical execution engine."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from ..protocols.registry import ProtocolRegistry
from .models import AnalysisRequest, AnalysisResult


class REngineError(Exception):
    """Base error for the R engine adapter."""


class REngineUnavailableError(REngineError):
    """Raised when Rscript cannot be located."""


class REngineExecutionError(REngineError):
    """Raised when the R subprocess fails."""


_R_SCRIPT = Path(__file__).resolve().parents[3] / "r_engine" / "run_analysis.R"


def find_rscript() -> str:
    configured = os.environ.get("RSCRIPT_PATH")
    if configured:
        return configured

    found = shutil.which("Rscript")
    if found:
        return found

    r_root = Path(os.environ.get("R_ROOT", "C:/Program Files/R"))
    if r_root.exists():
        candidates = sorted(r_root.glob("*/bin/Rscript.exe"), reverse=True)
        if candidates:
            return str(candidates[0])

    raise REngineUnavailableError(
        "Rscript not found. Set RSCRIPT_PATH or install R."
    )


def is_r_available() -> bool:
    try:
        find_rscript()
        return True
    except REngineUnavailableError:
        return False


def _r_libs_user() -> str | None:
    configured = os.environ.get("R_LIBS_USER")
    if configured:
        return configured
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = Path(local_app_data) / "R" / "win-library" / "4.6"
        if candidate.exists():
            return str(candidate)
    return None


class REngine:
    """Protocol-bound R execution engine."""

    def run(
        self,
        request: AnalysisRequest,
        registry: ProtocolRegistry | None = None,
    ) -> AnalysisResult:
        return run_analysis(request, registry=registry)


def run_analysis(
    request: AnalysisRequest,
    registry: ProtocolRegistry | None = None,
) -> AnalysisResult:
    registry = registry or ProtocolRegistry.load_default()
    protocol = registry.get(request.protocol_id)

    alpha = request.alpha if request.alpha is not None else protocol.alpha
    params: dict[str, Any] = {
        "protocol_id": request.protocol_id,
        "method": protocol.method.value,
        "outcome": request.outcome,
        "group": request.group,
        "factor2": request.factor2,
        "paired_by": request.paired_by,
        "predictors": list(request.predictors),
        "alpha": alpha,
        "variance": protocol.assumptions.variance.value,
    }

    rscript = find_rscript()
    with tempfile.TemporaryDirectory(prefix="researchstat-r-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_path = tmp_path / "data.csv"
        params_path = tmp_path / "params.json"
        output_path = tmp_path / "output.json"

        request.data.to_csv(data_path, index=False, encoding="utf-8")
        params_path.write_text(
            json.dumps(params, ensure_ascii=False), encoding="utf-8"
        )

        env = os.environ.copy()
        r_libs = _r_libs_user()
        if r_libs:
            env["R_LIBS_USER"] = r_libs

        completed = subprocess.run(
            [rscript, str(_R_SCRIPT), str(params_path), str(data_path), str(output_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=False,
        )

        if completed.returncode != 0:
            detail = completed.stderr.strip()
            if output_path.exists():
                try:
                    error_data = json.loads(output_path.read_text(encoding="utf-8"))
                    detail = error_data.get("error", detail)
                except json.JSONDecodeError:
                    pass
            raise REngineExecutionError(detail)

        output = json.loads(output_path.read_text(encoding="utf-8"))

    for key in ("statistics", "p_values", "effect_size", "parameters", "metadata"):
        if output.get(key) == []:
            output[key] = {}

    return AnalysisResult.model_validate(output)
