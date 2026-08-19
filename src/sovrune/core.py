"""Provider-neutral business state and operating-loop contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class Evidence:
    source: str
    as_of: str
    confidence: float

    def validate(self) -> None:
        if not self.source or not self.as_of:
            raise ValueError("evidence requires source and as_of")
        if not 0 <= self.confidence <= 1:
            raise ValueError("evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class Metric:
    name: str
    value: float | None
    unit: str
    target: float | None = None
    evidence: Evidence = field(default_factory=lambda: Evidence("unknown", "unknown", 0))

    def validate(self) -> None:
        if not self.name or not self.unit:
            raise ValueError("metric requires name and unit")
        self.evidence.validate()


@dataclass
class BusinessState:
    company: str
    north_star: Metric
    metrics: list[Metric]
    risks: list[dict[str, Any]] = field(default_factory=list)
    experiments: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def validate(self) -> None:
        if not self.company:
            raise ValueError("company is required")
        self.north_star.validate()
        for metric in self.metrics:
            metric.validate()

        # State sent to the operating layer contains aggregates, never records.
        forbidden = {"email", "phone", "address", "card", "password", "secret", "token"}
        keys: set[str] = set()

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    keys.add(str(key).lower())
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(asdict(self))
        leaked = sorted(keys & forbidden)
        if leaked:
            raise ValueError(f"business state contains forbidden keys: {', '.join(leaked)}")

    def confidence(self) -> float:
        values = [self.north_star.evidence.confidence, *(m.evidence.confidence for m in self.metrics)]
        return round(mean(values), 3) if values else 0

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["confidence"] = self.confidence()
        return data


@dataclass(frozen=True)
class OfficeResult:
    office: str
    status: str
    summary: str
    artifacts: list[dict[str, str]]
    requires_human: bool = False


class CompanyAdapter:
    """A company supplies aggregate state. Sovrune never reaches into production."""

    name = "company"

    def build_state(self) -> BusinessState:  # pragma: no cover - interface
        raise NotImplementedError
