"""Create durable operating runs that stop at a human approval boundary."""
from __future__ import annotations
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from .core import BusinessState, Metric
from .offices import constraint_metric, run_operating_loop
from .store import AccountabilityStore, now

def identifier(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def execute_run(state: BusinessState, store: AccountabilityStore) -> dict:
    state.validate()
    started = now()
    run_id = identifier("run")
    metric = constraint_metric(state)
    steps = run_operating_loop(state)
    artifacts = [{
        "id": identifier("art"), "office": step["office"],
        "kind": "office-result", "status": step["status"],
        "summary": step["summary"], "payload": step,
        "created_at": started,
    } for step in steps]
    baseline = metric.value
    target = metric.target
    evidence = [{"source": metric.evidence.source, "as_of": metric.evidence.as_of,
                 "confidence": metric.evidence.confidence, "metric": metric.name}]
    decision_id = identifier("dec")
    expected = _expected_outcome(metric)
    decision = {
        "id": decision_id, "title": f"Improve {metric.name}",
        "rationale": _rationale(metric), "evidence": evidence,
        "expected_outcome": expected, "status": "proposed", "created_at": started,
    }
    approval = {"id": identifier("apr"), "status": "pending", "requested_at": started}
    window_opens = (datetime.now(UTC) + timedelta(days=14)).date().isoformat()
    prediction = {
        "id": identifier("pred"), "metric": metric.name, "baseline": baseline,
        "target": target, "unit": metric.unit, "window_opens": window_opens,
        "status": "pending_approval", "created_at": started,
    }
    run = {"id": run_id, "company": state.company, "status": "awaiting_approval",
           "confidence": state.confidence(), "state": state.to_dict(), "started_at": started}
    store.create_run(run, artifacts, decision, approval, prediction)
    created = store.get_run(run_id)
    assert created is not None
    return created

def _gap(metric: Metric) -> float | None:
    if metric.value is None or metric.target is None:
        return None
    return metric.target - metric.value

def _rationale(metric: Metric) -> str:
    gap = _gap(metric)
    if gap is None:
        return f"{metric.name} is the highest-priority evidenced metric without a complete target gap."
    return f"{metric.name} is {abs(gap):g} {metric.unit} {'below' if gap >= 0 else 'above'} its declared target."

def _expected_outcome(metric: Metric) -> str:
    if metric.target is None or metric.value is None:
        return f"Establish and measure a target for {metric.name} within 14 days."
    return f"Move {metric.name} from {metric.value:g} to {metric.target:g} {metric.unit} by the measurement window."
