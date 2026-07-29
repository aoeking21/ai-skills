from __future__ import annotations

import hashlib

from .models import GenerationRequest, GenerationResult, PromptPackage, ValidationReport


class IdentityLockValidator:
    """Validate the identity-lock contract without biometric recognition.

    This component checks authorization, reference-file integrity, prompt propagation,
    and output-file integrity. Final visual identity similarity remains a human review.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    REQUIRED_POSITIVE_TERMS = ("identity_reference", "唯一人物身份参考", "脸型", "眉眼", "年龄感")
    REQUIRED_NEGATIVE_TERMS = ("身份漂移", "换脸", "混脸")

    def preflight(self, request: GenerationRequest) -> ValidationReport:
        checks: list[str] = []
        warnings: list[str] = []

        if request.identity_reference is None:
            checks.append("no identity reference supplied; identity lock is not applicable")
            return ValidationReport("not_applicable", checks, warnings)

        if not request.identity_authorized:
            raise ValueError("identity_reference requires identity_authorized=true")

        path = request.identity_reference.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"identity reference does not exist: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"unsupported identity reference format: {path.suffix}")
        if path.stat().st_size == 0:
            raise ValueError("identity reference is empty")

        checks.extend(
            [
                "identity reference exists",
                "identity authorization flag is present",
                "identity reference uses a supported image format",
            ]
        )
        warnings.append(
            "post-generation facial similarity requires manual review; no biometric identification is performed"
        )
        return ValidationReport("pass", checks, warnings)

    def validate_prompt_contract(
        self, request: GenerationRequest, package: PromptPackage
    ) -> ValidationReport:
        if request.identity_reference is None:
            return ValidationReport("not_applicable", ["no identity prompt contract required"], [])

        missing_positive = [
            term for term in self.REQUIRED_POSITIVE_TERMS if term not in package.positive_prompt
        ]
        missing_negative = [
            term for term in self.REQUIRED_NEGATIVE_TERMS if term not in package.negative_prompt
        ]
        if missing_positive or missing_negative:
            missing = ", ".join((*missing_positive, *missing_negative))
            raise ValueError(f"identity-lock prompt contract is incomplete: {missing}")

        return ValidationReport(
            "pass",
            [
                "identity lock propagated to positive prompt",
                "identity drift controls propagated to negative prompt",
            ],
            [],
        )

    def postflight(
        self, request: GenerationRequest, result: GenerationResult
    ) -> ValidationReport:
        if result.output_path is None:
            return ValidationReport("pass", ["adapter produced metadata-only output"], [])
        output = result.output_path.resolve()
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"adapter output is missing or empty: {output}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        checks = [
            f"output exists ({output.stat().st_size} bytes)",
            f"output sha256={digest}",
        ]
        if request.identity_reference:
            return ValidationReport(
                "manual_review_required",
                checks,
                ["compare the generated face with the authorized reference before publishing"],
            )
        return ValidationReport("pass", checks, [])
