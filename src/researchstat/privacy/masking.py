"""Field-level masking and temporary workspace cleanup."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


class PrivacyError(ValueError):
    """Raised for invalid privacy operations."""


def mask_columns(
    data: pd.DataFrame,
    columns: Sequence[str],
    replacement: str = "[REDACTED]",
) -> pd.DataFrame:
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise PrivacyError(f"Missing columns to mask: {', '.join(missing)}")
    work = data.copy()
    for column in columns:
        work[column] = replacement
    return work


def mask_identifiers(
    data: pd.DataFrame,
    columns: Sequence[str],
    salt: str = "",
) -> pd.DataFrame:
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise PrivacyError(f"Missing identifier columns: {', '.join(missing)}")
    work = data.copy()
    for column in columns:
        work[column] = work[column].astype(str).map(
            lambda value: hashlib.sha256(
                f"{salt}:{value}".encode("utf-8")
            ).hexdigest()[:16]
        )
    return work


@contextmanager
def temporary_workspace(
    prefix: str = "researchstat-",
    delete_on_exit: bool = True,
) -> Iterator[Path]:
    path = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield path
    finally:
        if delete_on_exit:
            shutil.rmtree(path, ignore_errors=True)


class TemporaryWorkspace:
    """Context manager wrapper for temporary analysis directories."""

    def __init__(self, prefix: str = "researchstat-") -> None:
        self.prefix = prefix
        self.path: Path | None = None

    def __enter__(self) -> Path:
        self.path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.path

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.path is not None:
            shutil.rmtree(self.path, ignore_errors=True)
