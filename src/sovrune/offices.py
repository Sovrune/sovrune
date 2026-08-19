"""Small, accountable office loop for the alpha."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .core import BusinessState, OfficeResult

def constraint_metric(state: BusinessState):
    """Choose the largest normalized target gap, falling back to the north star."""
    candidates = [metric for metric in state.metrics if metric.value is not None and metric.target is not None]
    if not candidates:
        return state.north_star
    def distance(metric):
        scale = abs(metric.target) or 1
        return abs(metric.target - metric.value) / scale
    return max(candidates, key=distance)


def run_operating_loop(state: BusinessState) -> list[dict[str, Any]]:
    state.validate()
    constraint = constraint_metric(state)
    gap = ((constraint.target or 0) - (constraint.value or 0)) if constraint.target is not None else None
    opportunity = (f"Closing the {abs(gap):g} {constraint.unit} gap is the highest-leverage opportunity."
                   if gap is not None else f"Establishing a target for {constraint.name} is the next measurable opportunity.")
    results = [
        OfficeResult("Signal", "complete", f"Business state assembled at {state.confidence():.0%} confidence.",
                     [{"type": "state", "id": "state-latest"}]),
        OfficeResult("Strategy", "complete", f"{constraint.name} is the binding constraint.",
                     [{"type": "constraint", "id": "binding-constraint"}]),
        OfficeResult("Opportunity", "complete", opportunity,
                     [{"type": "opportunity", "id": "opp-001"}]),
        OfficeResult("Product", "complete", f"Design a bounded experiment to improve {constraint.name}.",
                     [{"type": "decision", "id": "dec-001"}, {"type": "prediction", "id": "pred-001"}]),
        OfficeResult("Engineering", "waiting", "Implementation is ready for an isolated work branch.",
                     [{"type": "issue", "id": "issue-001"}]),
        OfficeResult("Approval", "human", "A human must approve any external write or deployment.", [], True),
        OfficeResult("Outcome", "scheduled", "Measure activation conversion after the declared observation window.",
                     [{"type": "experiment", "id": "exp-14"}]),
    ]
    return [asdict(result) for result in results]
