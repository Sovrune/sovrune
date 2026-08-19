"""Small, accountable office loop for the alpha."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .core import BusinessState, OfficeResult


def run_operating_loop(state: BusinessState) -> list[dict[str, Any]]:
    state.validate()
    values = {m.name: m for m in state.metrics}
    conversion = values["Proposal to activation"]
    gap = round((conversion.target or 0) - (conversion.value or 0), 3)
    results = [
        OfficeResult("Signal", "complete", f"Business state assembled at {state.confidence():.0%} confidence.",
                     [{"type": "state", "id": "state-latest"}]),
        OfficeResult("Strategy", "complete", "Proposal-to-activation is the binding constraint.",
                     [{"type": "constraint", "id": "proposal-to-activation"}]),
        OfficeResult("Opportunity", "complete", f"Closing the {gap:.1%} conversion gap is the highest-leverage opportunity.",
                     [{"type": "opportunity", "id": "opp-001"}]),
        OfficeResult("Product", "complete", "Test a reliable 48-hour proposal follow-up workflow.",
                     [{"type": "decision", "id": "dec-001"}, {"type": "prediction", "id": "pred-001"}]),
        OfficeResult("Engineering", "waiting", "Implementation is ready for an isolated work branch.",
                     [{"type": "issue", "id": "issue-001"}]),
        OfficeResult("Approval", "human", "A human must approve any external write or deployment.", [], True),
        OfficeResult("Outcome", "scheduled", "Measure activation conversion after the declared observation window.",
                     [{"type": "experiment", "id": "exp-14"}]),
    ]
    return [asdict(result) for result in results]
