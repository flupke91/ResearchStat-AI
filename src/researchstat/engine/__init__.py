"""Statistical execution engine."""

from .models import AnalysisRequest, AnalysisResult, AssumptionCheck, EngineInfo
from .python_engine import (
    EngineError,
    InvalidAnalysisInputError,
    PythonEngine,
    UnsupportedProtocolError,
    python_engine_info,
    run_analysis,
)
from .r_engine import (
    REngine,
    REngineError,
    REngineExecutionError,
    REngineUnavailableError,
    is_r_available,
    run_analysis as run_r_analysis,
)

__all__ = [
    "AnalysisRequest",
    "AnalysisResult",
    "AssumptionCheck",
    "EngineError",
    "EngineInfo",
    "InvalidAnalysisInputError",
    "PythonEngine",
    "REngine",
    "REngineError",
    "REngineExecutionError",
    "REngineUnavailableError",
    "UnsupportedProtocolError",
    "is_r_available",
    "python_engine_info",
    "run_analysis",
    "run_r_analysis",
]
