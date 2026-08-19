"""Public Company Adapter SDK: scaffold, load, and validate adapters."""
from __future__ import annotations
import importlib
import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from .core import BusinessState, CompanyAdapter

DEFAULT_ADAPTER = "sovrune.demo:AcmeAdapter"

class AdapterError(RuntimeError):
    """An adapter cannot be loaded or violates the SDK contract."""

@dataclass(frozen=True)
class ValidationReport:
    adapter: str
    company: str
    metrics: int
    confidence: float
    def summary(self) -> str:
        return f"valid adapter {self.adapter}: {self.company} · {self.metrics} metrics · confidence {self.confidence:.3f}"

def _load_module(reference: str) -> tuple[ModuleType, str]:
    if ":" not in reference:
        raise AdapterError("adapter must use module:Class or /path/to/file.py:Class")
    module_ref, class_name = reference.rsplit(":", 1)
    if not module_ref or not class_name:
        raise AdapterError("adapter must include both a module and class name")
    path = Path(module_ref).expanduser()
    if path.suffix == ".py" or path.exists():
        if not path.is_file():
            raise AdapterError(f"adapter file not found: {path}")
        spec = importlib.util.spec_from_file_location("sovrune_company_adapter", path.resolve())
        if not spec or not spec.loader:
            raise AdapterError(f"cannot import adapter file: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, class_name
    try:
        return importlib.import_module(module_ref), class_name
    except ImportError as error:
        raise AdapterError(f"cannot import adapter module: {module_ref}") from error

def load_adapter(reference: str | None = None) -> CompanyAdapter:
    selected = reference or os.getenv("SOVRUNE_COMPANY_ADAPTER", DEFAULT_ADAPTER)
    module, class_name = _load_module(selected)
    adapter_type = getattr(module, class_name, None)
    if not isinstance(adapter_type, type) or not issubclass(adapter_type, CompanyAdapter):
        raise AdapterError(f"{selected} must name a CompanyAdapter subclass")
    try:
        return adapter_type()
    except TypeError as error:
        raise AdapterError(f"{selected} must be constructible without arguments") from error

def validate_adapter(reference: str | None = None) -> ValidationReport:
    selected = reference or os.getenv("SOVRUNE_COMPANY_ADAPTER", DEFAULT_ADAPTER)
    adapter = load_adapter(selected)
    try:
        state = adapter.build_state()
    except Exception as error:
        raise AdapterError(f"{selected}.build_state() failed: {type(error).__name__}") from error
    if not isinstance(state, BusinessState):
        raise AdapterError(f"{selected}.build_state() must return BusinessState")
    state.validate()
    return ValidationReport(selected, state.company, len(state.metrics), state.confidence())

def scaffold_company(name: str, output: str | Path, provider: str = "ollama") -> tuple[Path, str]:
    """Create a minimal adapter project without writing or requesting credentials."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not slug:
        raise AdapterError("company name must contain a letter or number")
    target = Path(output).expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise AdapterError(f"output directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    class_name = "".join(part.capitalize() for part in slug.split("_")) + "Adapter"
    adapter_source = f'''"""Aggregate-only Sovrune adapter for {name}."""
from datetime import UTC, datetime
from sovrune import BusinessState, CompanyAdapter, Evidence, Metric

class {class_name}(CompanyAdapter):
    name = {name!r}
    def build_state(self) -> BusinessState:
        # Replace these fictional aggregates with reads from your analytics layer.
        # Never put customer rows, credentials, emails, or tokens in BusinessState.
        today = datetime.now(UTC).date().isoformat()
        evidence = Evidence("replace-with-source-name", today, 0.8)
        return BusinessState(
            company=self.name,
            north_star=Metric("Weekly active accounts", 120, "accounts", 150, evidence),
            metrics=[Metric("Activation rate", 0.42, "ratio", 0.5, evidence)],
            risks=[{{"id": "risk-1", "title": "Replace this fictional risk", "severity": "medium"}}],
        )
'''
    models = {"ollama": "qwen3", "openai-compatible": "gpt-5", "anthropic": "claude-sonnet-4-5", "gemini": "gemini-2.5-pro"}
    env_source = (f"SOVRUNE_COMPANY_ADAPTER={target / 'adapter.py'}:{class_name}\n"
                  f"SOVRUNE_PROVIDER={provider}\nSOVRUNE_MODEL={models.get(provider, 'qwen3')}\n"
                  "# Add provider credentials here only; never commit this file.\n")
    (target / "adapter.py").write_text(adapter_source)
    (target / ".env.example").write_text(env_source)
    (target / ".gitignore").write_text(".env\n__pycache__/\n")
    return target, class_name
