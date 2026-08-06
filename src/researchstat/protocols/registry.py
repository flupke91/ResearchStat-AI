"""YAML-backed statistical protocol registry."""

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .schema import PosthocMethod, Protocol, StatisticalMethod, VarianceAssumption


DEFAULT_PROTOCOLS_PATH = Path(__file__).parent / "data" / "v1.yaml"


class ProtocolRegistryError(Exception):
    """Base error for protocol registry operations."""


class ProtocolNotFoundError(ProtocolRegistryError, KeyError):
    """Raised when a requested protocol id does not exist."""


class DuplicateProtocolError(ProtocolRegistryError):
    """Raised when registering a protocol id that already exists."""


class ProtocolRegistry:
    def __init__(
        self, protocols: Sequence[Protocol | Mapping[str, Any]] | None = None
    ) -> None:
        self._protocols: dict[str, Protocol] = {}
        if protocols is not None:
            self.register_many(protocols)

    @classmethod
    def load_default(cls) -> "ProtocolRegistry":
        return cls.load_yaml(DEFAULT_PROTOCOLS_PATH)

    @classmethod
    def load_yaml(cls, path: str | Path) -> "ProtocolRegistry":
        with Path(path).open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        if isinstance(data, dict):
            data = data.get("protocols", [])
        if not isinstance(data, list):
            raise ProtocolRegistryError(
                f"Protocol YAML must contain a list or 'protocols' key: {path}"
            )
        return cls(data)

    def register(self, protocol: Protocol | Mapping[str, Any]) -> Protocol:
        parsed = (
            protocol
            if isinstance(protocol, Protocol)
            else Protocol.model_validate(protocol)
        )
        if parsed.id in self._protocols:
            raise DuplicateProtocolError(f"Duplicate protocol id: {parsed.id}")
        self._protocols[parsed.id] = parsed
        return parsed

    def register_many(
        self, protocols: Iterable[Protocol | Mapping[str, Any]]
    ) -> None:
        for protocol in protocols:
            self.register(protocol)

    def get(self, protocol_id: str) -> Protocol:
        try:
            return self._protocols[protocol_id]
        except KeyError as exc:
            raise ProtocolNotFoundError(
                f"Protocol not found: {protocol_id}"
            ) from exc

    def get_or_none(self, protocol_id: str) -> Protocol | None:
        return self._protocols.get(protocol_id)

    def list(self) -> list[Protocol]:
        return [self._protocols[key] for key in sorted(self._protocols)]

    def ids(self) -> list[str]:
        return [protocol.id for protocol in self.list()]

    def search(
        self,
        method: StatisticalMethod | str | None = None,
        posthoc: PosthocMethod | str | None = None,
        variance: VarianceAssumption | str | None = None,
        alpha: float | None = None,
    ) -> list[Protocol]:
        if isinstance(method, str):
            method = StatisticalMethod(method)
        if isinstance(posthoc, str):
            posthoc = PosthocMethod(posthoc)
        if isinstance(variance, str):
            variance = VarianceAssumption(variance)

        matches: list[Protocol] = []
        for protocol in self.list():
            if method is not None and protocol.method is not method:
                continue
            if posthoc is not None and protocol.posthoc is not posthoc:
                continue
            if variance is not None and protocol.assumptions.variance is not variance:
                continue
            if alpha is not None and protocol.alpha != alpha:
                continue
            matches.append(protocol)
        return matches

    def __len__(self) -> int:
        return len(self._protocols)

    def __contains__(self, protocol_id: str) -> bool:
        return protocol_id in self._protocols

    def __iter__(self):
        return iter(self.list())
