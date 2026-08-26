#!/usr/bin/env python3
"""Quality gate and bounded auto-repair for portrait outputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from portrait_master import PROTECTED_DOMAINS, GovernanceError


DEFAULT_MAX_REPAIR_ROUNDS = 2
REPAIR_GUIDANCE = {
    "identity": "restore identity from the current-upload reference",
    "age": "preserve the person's age structure",
    "face_geometry": "restore face geometry",
    "body_proportions": "restore body proportions",
    "distinctive_features": "restore distinctive features",
    "subject_count": "restore the subject count",
    "subject_mapping": "restore subject-to-position mapping",
    "clothing": "restore the original clothing",
    "safety": "re-run the safety review and confirm it passes",
    "scope": "restrict changes to the allowed change domains",
    "routing": "keep routing configuration unchanged",
    "fallback": "keep fallback configuration unchanged",
}


@dataclass(frozen=True)
class GateResult:
    domain: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityGateResult:
    status: str
    checks: tuple[GateResult, ...]
    repair_rounds: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": [check.to_dict() for check in self.checks],
            "repair_rounds": self.repair_rounds,
            "reason": self.reason,
        }


def _identity_checks(request: Mapping[str, Any], output: Mapping[str, Any]) -> list[GateResult]:
    requires_identity = request.get("requires_identity_preservation", True)
    checks = []
    if requires_identity:
        if output.get("identity_changed") is True:
            checks.append(GateResult("identity", False, "output declares an identity change"))
        elif not output.get("identity_source"):
            checks.append(GateResult("identity", False, "identity_source must be declared"))
    return checks


def _protected_domain_checks(request: Mapping[str, Any], output: Mapping[str, Any]) -> list[GateResult]:
    changed = set(str(domain) for domain in output.get("changed_domains", ()))
    checks = []
    for domain in PROTECTED_DOMAINS:
        declared = output.get(f"{domain}_changed") is True
        if domain in changed or declared:
            checks.append(GateResult(domain, False, f"output changes protected domain: {domain}"))
    return checks


def _subject_count_check(request: Mapping[str, Any], output: Mapping[str, Any]) -> GateResult | None:
    expected = request.get("subject_count")
    declared = output.get("subject_count")
    if expected is not None and declared is not None and int(declared) != int(expected):
        return GateResult("subject_count", False, f"subject count changed from {expected} to {declared}")
    return None


def _safety_checks(request: Mapping[str, Any], output: Mapping[str, Any]) -> list[GateResult]:
    checks = []
    if output.get("safety_reviewed") is not True:
        checks.append(GateResult("safety", False, "output must declare safety_reviewed"))
    if request.get("requires_identity_preservation", True) and request.get("identity_authorized") is not True:
        checks.append(GateResult("safety", False, "identity use must be authorized"))
    return checks


def _scope_check(request: Mapping[str, Any], output: Mapping[str, Any]) -> GateResult | None:
    allowed = set(str(domain) for domain in request.get("allowed_changes", ()))
    changed = set(str(domain) for domain in output.get("changed_domains", ()))
    unexpected = sorted(changed - allowed)
    if unexpected:
        return GateResult("scope", False, "changes outside allowed domains: " + ", ".join(unexpected))
    return None


def run_quality_gate(request: Mapping[str, Any], output: Mapping[str, Any]) -> QualityGateResult:
    collected: list[GateResult] = []
    collected.extend(_identity_checks(request, output))
    collected.extend(_protected_domain_checks(request, output))
    subject_count = _subject_count_check(request, output)
    if subject_count is not None:
        collected.append(subject_count)
    collected.extend(_safety_checks(request, output))
    scope = _scope_check(request, output)
    if scope is not None:
        collected.append(scope)

    checks: list[GateResult] = []
    seen: set[str] = set()
    for check in collected:
        if check.domain in seen:
            continue
        seen.add(check.domain)
        checks.append(check)
    passed = all(check.passed for check in checks)
    if passed:
        return QualityGateResult("passed", tuple(checks), 0, "all quality gates passed")
    failing = [check.domain for check in checks if not check.passed]
    return QualityGateResult("quality_gate_failed", tuple(checks), 0, "failing domains: " + ", ".join(failing))


def repair_instruction(result: QualityGateResult) -> dict[str, Any]:
    failing = [check for check in result.checks if not check.passed]
    return {
        "failing_domains": [check.domain for check in failing],
        "required_actions": [REPAIR_GUIDANCE[check.domain] for check in failing if check.domain in REPAIR_GUIDANCE],
    }


def auto_repair(
    request: Mapping[str, Any],
    producer: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
    max_repair_rounds: int | None = None,
) -> QualityGateResult:
    max_rounds = max_repair_rounds if max_repair_rounds is not None else DEFAULT_MAX_REPAIR_ROUNDS
    if max_rounds < 0:
        raise GovernanceError("max_repair_rounds must be non-negative")

    result = run_quality_gate(request, producer(request, {"repair_round": 0}))
    rounds = 0
    while result.status != "passed" and rounds < max_rounds:
        rounds += 1
        payload = {
            "repair_round": rounds,
            "quality_gate_feedback": repair_instruction(result),
        }
        result = run_quality_gate(request, producer(request, payload))

    if result.status == "passed":
        return QualityGateResult("passed", result.checks, rounds, f"passed after {rounds} repair round(s)")
    return QualityGateResult(
        "quality_gate_failed",
        result.checks,
        rounds,
        f"still failing after {max_rounds} repair round(s)",
    )


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    gate_parser = subparsers.add_parser("gate")
    gate_parser.add_argument("request")
    gate_parser.add_argument("output")
    args = parser.parse_args()
    if args.command == "gate":
        print(json.dumps(run_quality_gate(_load(args.request), _load(args.output)).to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
