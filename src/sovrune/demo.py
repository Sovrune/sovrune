"""Fictional, deterministic company used by the public demo."""

from datetime import UTC, datetime

from .core import BusinessState, CompanyAdapter, Evidence, Metric


class AcmeAdapter(CompanyAdapter):
    name = "Acme Solar"

    def build_state(self) -> BusinessState:
        today = datetime.now(UTC).date().isoformat()
        ev = Evidence("acme-demo-generated", today, 0.94)
        return BusinessState(
            company=self.name,
            north_star=Metric("Activated sites / week", 38, "sites", 50, ev),
            metrics=[
                Metric("Qualified visits", 12480, "visits", 15000, ev),
                Metric("Visit to assessment", 0.071, "ratio", 0.09, ev),
                Metric("Assessment to proposal", 0.43, "ratio", 0.55, ev),
                Metric("Proposal to activation", 0.10, "ratio", 0.16, ev),
                Metric("Support backlog", 47, "tickets", 20, ev),
                Metric("API p95 latency", 312, "ms", 250, ev),
            ],
            risks=[{"id": "risk-1", "title": "Proposal follow-up is inconsistent", "severity": "high"}],
            experiments=[{"id": "exp-14", "title": "48-hour proposal follow-up", "status": "measuring"}],
        )
