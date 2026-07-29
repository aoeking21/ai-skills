from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .adapters import ImageModelAdapter
from .identity_lock import IdentityLockValidator
from .models import GenerationRequest, GenerationResult
from .prompt_builder import PromptBuilder


class GenerationPipeline:
    """Knowledge base -> rules -> validation -> adapter -> result manifest."""

    def __init__(
        self,
        skill_root: Path,
        adapter: ImageModelAdapter,
        *,
        identity_validator: IdentityLockValidator | None = None,
    ) -> None:
        self.skill_root = skill_root.resolve()
        self.prompt_builder = PromptBuilder(self.skill_root)
        self.identity_validator = identity_validator or IdentityLockValidator()
        self.adapter = adapter

    def run(self, request: GenerationRequest) -> GenerationResult:
        preflight = self.identity_validator.preflight(request)
        package = self.prompt_builder.build(request)
        contract = self.identity_validator.validate_prompt_contract(request, package)
        result = self.adapter.generate(request, package)
        postflight = self.identity_validator.postflight(request, result)

        request.output_dir.mkdir(parents=True, exist_ok=True)
        manifest = request.output_dir / f"{request.output_name}.manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "skill_root": str(self.skill_root),
                    "request": request.to_dict(),
                    "prompt_package": package.to_dict(),
                    "identity_validation": {
                        "preflight": preflight.to_dict(),
                        "prompt_contract": contract.to_dict(),
                        "postflight": postflight.to_dict(),
                    },
                    "generation": result.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        result.manifest_path = manifest
        result.metadata["identity_review_status"] = postflight.status
        result.metadata["selected_route"] = package.route_id
        result.metadata["selected_overlay"] = package.overlay_id
        return result
