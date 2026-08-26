from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from portrait_master import (
    ExternalAdapterUnavailable,
    GovernanceError,
    RembrandtExternalAdapter,
    resolve_reference_profile,
    validate_manifest,
    validate_profile,
)


class FakeRunner:
    def __init__(self, changed_domains):
        self.changed_domains = changed_domains

    def invoke(self, skill_name, payload):
        return {"skill": skill_name, "changed_domains": self.changed_domains, "payload": dict(payload)}


class MissingRunner:
    def invoke(self, skill_name, payload):
        raise ExternalAdapterUnavailable("rembrandt-portrait-lighting is not installed")


class ManifestTests(unittest.TestCase):
    def test_repository_manifest_enforces_zero_global_identity_assets(self):
        manifest = json.loads((SKILL_ROOT / "data/visual-asset-manifest-v1.0.json").read_text(encoding="utf-8"))
        validate_manifest(manifest)
        self.assertEqual(manifest["completion_status"], "complete_runtime_manifest")
        self.assertEqual(manifest["asset_records"], [])

    def test_model_generated_cannot_be_verified(self):
        manifest = {
            "schema_version": "1.0",
            "scope": "portrait_master_runtime_routable_assets",
            "completion_status": "complete_runtime_manifest",
            "source_policy": "read_only_no_delete",
            "runtime_policy": {
                "global_identity_assets": 0,
                "current_upload_is_primary": True,
                "profiles_require_explicit_activation": True,
            },
            "asset_records": [{"provenance": "model_generated", "identity_authority": "verified", "profile_scope": "person-a"}],
        }
        with self.assertRaisesRegex(GovernanceError, "model-generated"):
            validate_manifest(manifest)

    def test_exact_duplicate_requires_sha256(self):
        manifest = {
            "schema_version": "1.0",
            "scope": "portrait_master_runtime_routable_assets",
            "completion_status": "complete_runtime_manifest",
            "source_policy": "read_only_no_delete",
            "runtime_policy": {
                "global_identity_assets": 0,
                "current_upload_is_primary": True,
                "profiles_require_explicit_activation": True,
            },
            "asset_records": [{"provenance": "provenance_unknown", "identity_authority": "none", "profile_scope": None, "exact_duplicate_group": "EDG-001", "sha256": None}],
        }
        with self.assertRaisesRegex(GovernanceError, "SHA-256"):
            validate_manifest(manifest)

    def test_mimi_album_assets_cannot_enter_runtime_manifest(self):
        manifest = {
            "schema_version": "1.0",
            "scope": "portrait_master_runtime_routable_assets",
            "completion_status": "complete_runtime_manifest",
            "source": "ChatGPT Library /咪咪的影集",
            "source_policy": "read_only_no_delete",
            "runtime_policy": {
                "global_identity_assets": 0,
                "current_upload_is_primary": True,
                "profiles_require_explicit_activation": True,
            },
            "asset_records": [{"provenance": "provenance_unknown", "identity_authority": "none", "profile_scope": None}],
        }
        with self.assertRaisesRegex(GovernanceError, "archive-only"):
            validate_manifest(manifest)


class ProfileTests(unittest.TestCase):
    def valid_profile(self):
        return {
            "schema_version": "1.0",
            "profile_id": "person-a",
            "explicit_activation_required": True,
            "references": [{"asset_id": "A-1", "role": "verified_feature", "provenance": "user_confirmed_real_original", "identity_authority": "verified"}],
        }

    def test_verified_feature_requires_real_original(self):
        profile = {
            "schema_version": "1.0",
            "profile_id": "person-a",
            "explicit_activation_required": True,
            "references": [{"asset_id": "A-1", "role": "verified_feature", "provenance": "model_generated", "identity_authority": "none"}],
        }
        with self.assertRaisesRegex(GovernanceError, "verified_feature"):
            validate_profile(profile)

    def test_no_profile_is_loaded_automatically(self):
        resolution = resolve_reference_profile(
            {"identity_reference": "/private/current-upload.jpg"},
            {"person-a": self.valid_profile()},
        )
        self.assertIsNone(resolution.profile_id)
        self.assertEqual(resolution.supplemental_asset_ids, ())

    def test_explicit_profile_adds_only_supplemental_references(self):
        resolution = resolve_reference_profile(
            {
                "identity_reference": "/private/current-upload.jpg",
                "profile_id": "person-a",
                "profile_activation_explicit": True,
            },
            {"person-a": self.valid_profile()},
        )
        self.assertEqual(resolution.identity_source, "current_upload")
        self.assertEqual(resolution.supplemental_asset_ids, ("A-1",))

    def test_profile_cannot_activate_implicitly(self):
        with self.assertRaisesRegex(GovernanceError, "must be explicit"):
            resolve_reference_profile(
                {"identity_reference": "/private/current-upload.jpg", "profile_id": "person-a"},
                {"person-a": self.valid_profile()},
            )


class RembrandtAdapterTests(unittest.TestCase):
    def base_request(self):
        return {
            "prompt": "请使用伦勃朗光重新打光",
            "lighting_mode": "relight",
            "task_mode": "identity_preserving_edit",
            "identity_reference": "/private/current-upload.jpg",
            "identity_authorized": True,
            "composition_mode": "preserve",
        }

    def test_preserve_source_never_delegates(self):
        request = self.base_request()
        request["lighting_mode"] = "preserve-source"
        self.assertEqual(RembrandtExternalAdapter.prepare(request).status, "not_applicable")

    def test_background_is_not_delegated_by_default(self):
        plan = RembrandtExternalAdapter.prepare(self.base_request())
        self.assertEqual(plan.delegated_domains, ("lighting",))
        self.assertEqual(plan.payload["identity_source"], "current_upload")

    def test_external_scope_violation_is_rejected(self):
        with self.assertRaisesRegex(GovernanceError, "scope_violation"):
            RembrandtExternalAdapter.execute(self.base_request(), FakeRunner(["lighting", "identity"]))

    def test_explicit_studio_background_can_be_delegated(self):
        request = self.base_request()
        request["allow_studio_background"] = True
        result = RembrandtExternalAdapter.execute(request, FakeRunner(["lighting", "background"]))
        self.assertEqual(result["status"], "completed")

    def test_missing_external_skill_is_explicit(self):
        result = RembrandtExternalAdapter.execute(self.base_request(), MissingRunner())
        self.assertEqual(result["status"], "external_adapter_unavailable")


if __name__ == "__main__":
    unittest.main()
