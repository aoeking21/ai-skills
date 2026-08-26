from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from portrait_master import GovernanceError
from quality_gate import auto_repair, repair_instruction, run_quality_gate


class QualityGateTests(unittest.TestCase):
    def base_request(self):
        return {
            "requires_identity_preservation": True,
            "identity_authorized": True,
            "allowed_changes": ["lighting", "background"],
            "subject_count": 1,
        }

    def valid_output(self, **overrides):
        output = {
            "identity_source": "current_upload",
            "identity_changed": False,
            "changed_domains": ["lighting"],
            "safety_reviewed": True,
            "subject_count": 1,
        }
        output.update(overrides)
        return output

    def test_valid_output_passes(self):
        result = run_quality_gate(self.base_request(), self.valid_output())
        self.assertEqual(result.status, "passed")
        self.assertTrue(all(check.passed for check in result.checks))

    def test_identity_change_fails(self):
        result = run_quality_gate(self.base_request(), self.valid_output(identity_changed=True))
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertIn("identity", result.reason)

    def test_missing_identity_source_fails(self):
        result = run_quality_gate(self.base_request(), self.valid_output(identity_source=None))
        self.assertEqual(result.status, "quality_gate_failed")
        details = [check.detail for check in result.checks if check.domain == "identity"]
        self.assertTrue(any("identity_source" in detail for detail in details))

    def test_protected_age_domain_fails(self):
        result = run_quality_gate(self.base_request(), self.valid_output(changed_domains=["lighting", "age"]))
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertIn("age", result.reason)

    def test_safety_not_reviewed_fails(self):
        result = run_quality_gate(self.base_request(), self.valid_output(safety_reviewed=False))
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertIn("safety", result.reason)

    def test_unexpected_change_domain_fails_scope(self):
        result = run_quality_gate(self.base_request(), self.valid_output(changed_domains=["style"]))
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertIn("scope", result.reason)

    def test_subject_count_mismatch_fails(self):
        result = run_quality_gate(self.base_request(), self.valid_output(subject_count=2))
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertIn("subject_count", result.reason)

    def test_repair_instruction_lists_failing_domains(self):
        result = run_quality_gate(self.base_request(), self.valid_output(identity_changed=True, safety_reviewed=False))
        instruction = repair_instruction(result)
        self.assertEqual(set(instruction["failing_domains"]), {"identity", "safety"})
        self.assertTrue(instruction["required_actions"])

    def test_auto_repair_passes_after_round(self):
        calls = []

        def producer(request: Mapping[str, Any], payload: Mapping[str, Any]) -> Mapping[str, Any]:
            calls.append(payload)
            if payload.get("repair_round") >= 1:
                return self.valid_output()
            return self.valid_output(identity_changed=True)

        result = auto_repair(self.base_request(), producer)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.repair_rounds, 1)
        self.assertEqual(len(calls), 2)

    def test_auto_repair_bounded(self):
        def producer(request: Mapping[str, Any], payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return self.valid_output(identity_changed=True)

        result = auto_repair(self.base_request(), producer, max_repair_rounds=2)
        self.assertEqual(result.status, "quality_gate_failed")
        self.assertEqual(result.repair_rounds, 2)
        self.assertIn("after 2 repair round", result.reason)

    def test_auto_repair_carries_feedback(self):
        payloads: list[Mapping[str, Any]] = []

        def producer(request: Mapping[str, Any], payload: Mapping[str, Any]) -> Mapping[str, Any]:
            payloads.append(payload)
            return self.valid_output(identity_changed=True)

        auto_repair(self.base_request(), producer, max_repair_rounds=1)
        self.assertEqual(payloads[1]["repair_round"], 1)
        self.assertEqual(payloads[1]["quality_gate_feedback"]["failing_domains"], ["identity"])

    def test_negative_max_rounds_rejected(self):
        with self.assertRaisesRegex(GovernanceError, "non-negative"):
            auto_repair(self.base_request(), lambda request, payload: self.valid_output(), max_repair_rounds=-1)


if __name__ == "__main__":
    unittest.main()
