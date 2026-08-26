#!/usr/bin/env python3
"""Validate asset/profile governance and isolate an external Rembrandt skill."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


class GovernanceError(ValueError):
    pass


class ExternalAdapterUnavailable(RuntimeError):
    pass


class ExternalSkillRunner(Protocol):
    def invoke(self, skill_name: str, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class AdapterPlan:
    status: str
    adapter: str
    external_skill: str | None
    delegated_domains: tuple[str, ...]
    protected_domains: tuple[str, ...]
    payload: dict[str, Any]
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["delegated_domains"] = list(self.delegated_domains)
        value["protected_domains"] = list(self.protected_domains)
        return value


@dataclass(frozen=True)
class ReferenceResolution:
    identity_source: str
    primary_reference: str | None
    profile_id: str | None
    supplemental_asset_ids: tuple[str, ...]


def resolve_reference_profile(
    request: Mapping[str, Any], profiles: Mapping[str, Mapping[str, Any]]
) -> ReferenceResolution:
    current_upload = request.get("identity_reference")
    if request.get("requires_identity_preservation", True) and not current_upload:
        raise GovernanceError("identity-preserving tasks require a current-upload reference")

    profile_id = request.get("profile_id")
    if not profile_id:
        return ReferenceResolution("current_upload", current_upload, None, ())
    if request.get("profile_activation_explicit") is not True:
        raise GovernanceError("reference profile activation must be explicit in the current request")
    profile = profiles.get(str(profile_id))
    if profile is None:
        raise GovernanceError(f"reference profile not found: {profile_id}")
    validate_profile(profile)
    if profile.get("profile_id") != profile_id:
        raise GovernanceError("reference profile ID does not match the requested profile")

    supplemental = tuple(
        str(reference["asset_id"])
        for reference in profile.get("references", [])
        if reference.get("role") in {"verified_identity", "verified_feature"}
    )
    return ReferenceResolution("current_upload", current_upload, str(profile_id), supplemental)


PROTECTED_DOMAINS = (
    "identity", "age", "face_geometry", "body_proportions",
    "distinctive_features", "subject_count", "subject_mapping", "clothing",
    "safety", "routing", "fallback",
)


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != "1.0":
        raise GovernanceError("manifest schema_version must be 1.0")
    if manifest.get("scope") != "portrait_master_runtime_routable_assets":
        raise GovernanceError("manifest scope must be runtime-routable assets")
    if manifest.get("completion_status") != "complete_runtime_manifest":
        raise GovernanceError("runtime manifest must be complete")
    if manifest.get("source_policy") != "read_only_no_delete":
        raise GovernanceError("source must remain read-only with no deletion")
    runtime = manifest.get("runtime_policy") or {}
    if runtime.get("global_identity_assets") != 0:
        raise GovernanceError("global identity asset count must be zero")
    if runtime.get("current_upload_is_primary") is not True:
        raise GovernanceError("current upload must be the primary identity source")
    if runtime.get("profiles_require_explicit_activation") is not True:
        raise GovernanceError("reference profiles must require explicit activation")

    for record in manifest.get("asset_records", []):
        provenance = record.get("provenance")
        authority = record.get("identity_authority")
        scope = record.get("profile_scope")
        if provenance == "model_generated" and authority != "none":
            raise GovernanceError("model-generated assets cannot have identity authority")
        if authority == "verified" and provenance != "user_confirmed_real_original":
            raise GovernanceError("verified identity requires a user-confirmed real original")
        if authority in {"candidate", "verified"} and (not scope or scope == "global"):
            raise GovernanceError("identity references must belong to an isolated profile")
        if record.get("exact_duplicate_group") and not record.get("sha256"):
            raise GovernanceError("exact duplicate groups require SHA-256 evidence")
    if manifest.get("source") == "ChatGPT Library /咪咪的影集" and manifest.get("asset_records"):
        raise GovernanceError("Mimi album assets must remain archive-only and outside the runtime manifest")


def validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema_version") != "1.0":
        raise GovernanceError("profile schema_version must be 1.0")
    if profile.get("explicit_activation_required") is not True:
        raise GovernanceError("profile must require explicit activation")
    for reference in profile.get("references", []):
        provenance = reference.get("provenance")
        authority = reference.get("identity_authority")
        role = reference.get("role")
        if provenance == "model_generated" and authority != "none":
            raise GovernanceError("model-generated profile references cannot carry identity authority")
        if role in {"verified_identity", "verified_feature"}:
            if provenance != "user_confirmed_real_original" or authority != "verified":
                raise GovernanceError(f"{role} requires verified real-original evidence")


class RembrandtExternalAdapter:
    name = "rembrandt-external-v1"
    external_skill = "rembrandt-portrait-lighting"

    @staticmethod
    def prepare(request: Mapping[str, Any]) -> AdapterPlan:
        prompt = str(request.get("prompt", "")).lower()
        explicit = "rembrandt" in prompt or "伦勃朗" in prompt
        lighting_mode = request.get("lighting_mode", "auto")
        task_mode = request.get("task_mode", "identity_preserving_edit")
        identity_reference = request.get("identity_reference")
        identity_authorized = request.get("identity_authorized") is True

        if not explicit:
            return AdapterPlan("not_applicable", RembrandtExternalAdapter.name, None, (), PROTECTED_DOMAINS, {}, "no explicit Rembrandt request")
        if lighting_mode != "relight" or task_mode in {"restoration", "preserve_source"}:
            return AdapterPlan("not_applicable", RembrandtExternalAdapter.name, None, (), PROTECTED_DOMAINS, {}, "task does not permit relighting")
        if not identity_reference or not identity_authorized:
            raise GovernanceError("Rembrandt relighting requires an authorized current-upload identity reference")

        allow_studio_background = request.get("allow_studio_background") is True
        delegated = ("lighting", "background") if allow_studio_background else ("lighting",)
        payload = {
            "task": "rembrandt portrait relighting",
            "identity_reference": identity_reference,
            "identity_source": "current_upload",
            "preserve": list(PROTECTED_DOMAINS),
            "allowed_changes": list(delegated),
            "background_mode": "studio_conversion" if allow_studio_background else "preserve",
            "composition_mode": request.get("composition_mode", "preserve"),
        }
        return AdapterPlan("ready", RembrandtExternalAdapter.name, RembrandtExternalAdapter.external_skill, delegated, PROTECTED_DOMAINS, payload)

    @classmethod
    def execute(cls, request: Mapping[str, Any], runner: ExternalSkillRunner) -> Mapping[str, Any]:
        plan = cls.prepare(request)
        if plan.status != "ready" or not plan.external_skill:
            return {"status": plan.status, "plan": plan.to_dict()}
        try:
            result = dict(runner.invoke(plan.external_skill, plan.payload))
        except ExternalAdapterUnavailable as exc:
            return {
                "status": "external_adapter_unavailable",
                "plan": plan.to_dict(),
                "reason": str(exc),
            }
        changed = set(result.get("changed_domains", ()))
        allowed = set(plan.delegated_domains)
        if not changed <= allowed:
            raise GovernanceError("external_adapter_scope_violation: " + ", ".join(sorted(changed - allowed)))
        return {"status": "completed", "plan": plan.to_dict(), "result": result}


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    manifest_parser = subparsers.add_parser("validate-manifest")
    manifest_parser.add_argument("path")
    profile_parser = subparsers.add_parser("validate-profile")
    profile_parser.add_argument("path")
    adapter_parser = subparsers.add_parser("plan-rembrandt")
    adapter_parser.add_argument("path")
    args = parser.parse_args()

    if args.command == "validate-manifest":
        validate_manifest(_load(args.path))
        print("Visual Asset Manifest governance passed.")
    elif args.command == "validate-profile":
        validate_profile(_load(args.path))
        print("Reference Profile governance passed.")
    else:
        print(json.dumps(RembrandtExternalAdapter.prepare(_load(args.path)).to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
