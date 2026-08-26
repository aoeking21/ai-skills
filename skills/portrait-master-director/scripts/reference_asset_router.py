#!/usr/bin/env python3
"""Route current-upload and explicitly activated profile assets by role."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from portrait_master import GovernanceError, validate_profile


ROUTABLE_NON_AUTHORITATIVE_ROLES = ("composition", "lighting", "style")
IDENTITY_ROLES = ("verified_identity", "verified_feature")
BLOCKED_TASK_MODES = ("restoration", "preserve_source", "preserve")
ALLOWED_ROLES = {*IDENTITY_ROLES, *ROUTABLE_NON_AUTHORITATIVE_ROLES}


@dataclass(frozen=True)
class RoutedAsset:
    asset_id: str
    role: str
    source: str
    provenance: str
    identity_authority: str
    profile_id: str | None
    enabled: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RejectedAsset:
    asset_id: str
    role: str
    profile_id: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDecision:
    routed: tuple[RoutedAsset, ...]
    rejected: tuple[RejectedAsset, ...]
    deduplicated: tuple[str, ...]
    profile_id: str | None
    identity_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "routed": [asset.to_dict() for asset in self.routed],
            "rejected": [asset.to_dict() for asset in self.rejected],
            "deduplicated": list(self.deduplicated),
            "profile_id": self.profile_id,
            "identity_source": self.identity_source,
        }


def _influence_enabled(role: str, request: Mapping[str, Any]) -> bool:
    if role in IDENTITY_ROLES:
        return True
    domain = {
        "composition": "composition",
        "lighting": "lighting",
        "style": "style",
    }.get(role)
    if domain is None:
        return False
    if request.get("task_mode", "identity_preserving_edit") in BLOCKED_TASK_MODES:
        return False
    allowed = set(str(item) for item in request.get("allowed_changes", ()))
    return domain in allowed


def _duplicate_groups(asset_id: str, known: Mapping[str, Any]) -> frozenset[str]:
    entry = known.get(asset_id)
    if not entry:
        return frozenset()
    groups = []
    for key in ("exact_duplicate_group", "visual_duplicate_group"):
        value = entry.get(key)
        if value:
            groups.append(str(value))
    return frozenset(groups)


def route_assets(
    request: Mapping[str, Any],
    profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> RoutingDecision:
    profiles = profiles or {}
    current_upload = request.get("identity_reference")
    requires_identity = request.get("requires_identity_preservation", True)
    if requires_identity and not current_upload:
        raise GovernanceError("identity-preserving tasks require a current-upload reference")

    routed: list[RoutedAsset] = []
    rejected: list[RejectedAsset] = []
    deduplicated: list[str] = []
    seen_groups: set[str] = set()
    known = request.get("known_duplicates", {})
    profile_id: str | None = None

    if current_upload:
        routed.append(
            RoutedAsset(
                asset_id=str(current_upload),
                role="identity_primary",
                source="current_upload",
                provenance="user_confirmed_real_original",
                identity_authority="verified",
                profile_id=None,
                enabled=True,
                reason="current upload is the primary identity source",
            )
        )
        seen_groups.update(_duplicate_groups(str(current_upload), known))

    requested_profile = request.get("profile_id")
    if not requested_profile:
        return RoutingDecision(tuple(routed), tuple(rejected), tuple(deduplicated), None, "current_upload")
    if request.get("profile_activation_explicit") is not True:
        raise GovernanceError("reference profile activation must be explicit in the current request")
    profile = profiles.get(str(requested_profile))
    if profile is None:
        raise GovernanceError(f"reference profile not found: {requested_profile}")
    if profile.get("profile_id") != str(requested_profile):
        raise GovernanceError("reference profile ID does not match the requested profile")
    validate_profile(profile)

    profile_id = str(requested_profile)
    for reference in profile.get("references", []):
        asset_id = str(reference.get("asset_id"))
        role = reference.get("role")
        if role not in ALLOWED_ROLES:
            raise GovernanceError(f"unsupported reference role: {role}")
        provenance = reference.get("provenance", "provenance_unknown")
        authority = reference.get("identity_authority", "none")

        if role in IDENTITY_ROLES and not current_upload:
            rejected.append(
                RejectedAsset(asset_id, role, profile_id, "no current-upload identity source for this task")
            )
            continue

        groups = _duplicate_groups(asset_id, known)
        if groups and groups & seen_groups:
            deduplicated.append(asset_id)
            continue
        seen_groups.update(groups)
        routed.append(
            RoutedAsset(
                asset_id=asset_id,
                role=role,
                source="profile",
                provenance=provenance,
                identity_authority=authority,
                profile_id=profile_id,
                enabled=_influence_enabled(role, request),
                reason="explicit profile reference",
            )
        )

    return RoutingDecision(tuple(routed), tuple(rejected), tuple(deduplicated), profile_id, "current_upload")


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--profiles", help="JSON file mapping profile_id to profile objects")
    args = parser.parse_args()
    request = _load(args.request)
    profiles = _load(args.profiles) if args.profiles else {}
    print(json.dumps(route_assets(request, profiles).to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
