from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass
class GenerationRequest:
    """A normalized request consumed by the generation pipeline."""

    task: str
    requirements: tuple[str, ...] = ()
    aspect_ratio: str = "9:16"
    route_id: str | None = None
    overlay_id: str | None = None
    identity_reference: Path | None = None
    identity_authorized: bool = False
    output_dir: Path = Path("outputs")
    output_name: str = "generation"
    extra_negative: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GenerationRequest":
        if not str(data.get("task", "")).strip():
            raise ValueError("request.task is required")
        identity_reference = data.get("identity_reference")
        return cls(
            task=str(data["task"]).strip(),
            requirements=tuple(str(item).strip() for item in data.get("requirements", ()) if str(item).strip()),
            aspect_ratio=str(data.get("aspect_ratio", "9:16")).strip() or "9:16",
            route_id=(str(data["route_id"]).strip() if data.get("route_id") else None),
            overlay_id=(str(data["overlay_id"]).strip() if data.get("overlay_id") else None),
            identity_reference=(Path(identity_reference).expanduser() if identity_reference else None),
            identity_authorized=bool(data.get("identity_authorized", False)),
            output_dir=Path(data.get("output_dir", "outputs")).expanduser(),
            output_name=str(data.get("output_name", "generation")).strip() or "generation",
            extra_negative=tuple(str(item).strip() for item in data.get("extra_negative", ()) if str(item).strip()),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["identity_reference"] = str(self.identity_reference) if self.identity_reference else None
        result["output_dir"] = str(self.output_dir)
        result["requirements"] = list(self.requirements)
        result["extra_negative"] = list(self.extra_negative)
        return result


@dataclass
class PromptPackage:
    positive_prompt: str
    negative_prompt: str
    route_id: str
    route_name: str
    overlay_id: str | None
    rules_loaded: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    status: str
    checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in {"pass", "manual_review_required", "not_applicable"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationResult:
    status: str
    adapter: str
    output_path: Path | None = None
    manifest_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "adapter": self.adapter,
            "output_path": str(self.output_path) if self.output_path else None,
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "metadata": self.metadata,
        }
