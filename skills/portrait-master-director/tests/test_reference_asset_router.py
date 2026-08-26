from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from portrait_master import GovernanceError
from reference_asset_router import route_assets


class ReferenceAssetRouterTests(unittest.TestCase):
    def base_request(self):
        return {
            "identity_reference": "current-upload.jpg",
            "requires_identity_preservation": True,
            "task_mode": "identity_preserving_edit",
            "allowed_changes": ["lighting"],
        }

    def valid_profile(self):
        return {
            "schema_version": "1.0",
            "profile_id": "person-a",
            "explicit_activation_required": True,
            "references": [
                {"asset_id": "A-1", "role": "verified_identity", "provenance": "user_confirmed_real_original", "identity_authority": "verified"},
                {"asset_id": "A-2", "role": "verified_feature", "provenance": "user_confirmed_real_original", "identity_authority": "verified"},
                {"asset_id": "A-3", "role": "lighting", "provenance": "model_generated", "identity_authority": "none"},
            ],
        }

    def test_no_profile_routes_only_current_upload(self):
        decision = route_assets(self.base_request(), {})
        self.assertEqual([asset.role for asset in decision.routed], ["identity_primary"])
        self.assertIsNone(decision.profile_id)
        self.assertEqual(decision.deduplicated, ())

    def test_explicit_profile_routes_supplemental_references(self):
        request = self.base_request()
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        decision = route_assets(request, {"person-a": self.valid_profile()})
        roles = [asset.role for asset in decision.routed]
        self.assertEqual(roles, ["identity_primary", "verified_identity", "verified_feature", "lighting"])
        self.assertEqual(decision.profile_id, "person-a")

    def test_profile_cannot_activate_implicitly(self):
        request = self.base_request()
        request["profile_id"] = "person-a"
        with self.assertRaisesRegex(GovernanceError, "must be explicit"):
            route_assets(request, {"person-a": self.valid_profile()})

    def test_identity_roles_rejected_without_current_upload(self):
        request = self.base_request()
        request["identity_reference"] = None
        request["requires_identity_preservation"] = False
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        decision = route_assets(request, {"person-a": self.valid_profile()})
        self.assertEqual([asset.role for asset in decision.routed], ["lighting"])
        self.assertEqual({item.asset_id for item in decision.rejected}, {"A-1", "A-2"})
        self.assertTrue(all(item.reason.startswith("no current-upload") for item in decision.rejected))

    def test_preserve_source_disables_lighting_reference(self):
        request = self.base_request()
        request["task_mode"] = "preserve_source"
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        decision = route_assets(request, {"person-a": self.valid_profile()})
        lighting = next(asset for asset in decision.routed if asset.role == "lighting")
        self.assertFalse(lighting.enabled)

    def test_allowed_changes_control_non_authoritative_roles(self):
        request = self.base_request()
        request["allowed_changes"] = []
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        decision = route_assets(request, {"person-a": self.valid_profile()})
        lighting = next(asset for asset in decision.routed if asset.role == "lighting")
        self.assertFalse(lighting.enabled)

    def test_exact_duplicate_of_current_upload_is_deduplicated(self):
        request = self.base_request()
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        request["known_duplicates"] = {
            "current-upload.jpg": {"exact_duplicate_group": "EDG-7"},
            "A-1": {"exact_duplicate_group": "EDG-7"},
        }
        decision = route_assets(request, {"person-a": self.valid_profile()})
        self.assertEqual(decision.deduplicated, ("A-1",))
        self.assertNotIn("A-1", [asset.asset_id for asset in decision.routed])

    def test_visual_duplicate_within_profile_is_deduplicated(self):
        request = self.base_request()
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        profile = self.valid_profile()
        profile["references"].append(
            {"asset_id": "A-4", "role": "verified_feature", "provenance": "user_confirmed_real_original", "identity_authority": "verified"}
        )
        request["known_duplicates"] = {
            "A-2": {"visual_duplicate_group": "VDG-3"},
            "A-4": {"visual_duplicate_group": "VDG-3"},
        }
        decision = route_assets(request, {"person-a": profile})
        self.assertEqual(decision.deduplicated, ("A-4",))

    def test_unsupported_role_is_rejected(self):
        request = self.base_request()
        request["profile_id"] = "person-a"
        request["profile_activation_explicit"] = True
        profile = self.valid_profile()
        profile["references"].append({"asset_id": "A-9", "role": "face_swap", "provenance": "provenance_unknown", "identity_authority": "none"})
        with self.assertRaisesRegex(GovernanceError, "unsupported reference role"):
            route_assets(request, {"person-a": profile})


if __name__ == "__main__":
    unittest.main()
