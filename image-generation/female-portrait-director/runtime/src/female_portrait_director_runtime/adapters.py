from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Protocol

from .models import GenerationRequest, GenerationResult, PromptPackage


class ImageModelAdapter(Protocol):
    name: str

    def generate(
        self, request: GenerationRequest, package: PromptPackage
    ) -> GenerationResult:
        ...


class DryRunAdapter:
    """Write the model payload without contacting an external image service."""

    name = "dry-run"

    def generate(
        self, request: GenerationRequest, package: PromptPackage
    ) -> GenerationResult:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        output = request.output_dir / f"{request.output_name}.prompt.json"
        output.write_text(
            json.dumps(
                {"request": request.to_dict(), "prompt_package": package.to_dict()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return GenerationResult(
            status="dry_run",
            adapter=self.name,
            output_path=output,
            metadata={
                "message": "prompt package created; no external image API was called"
            },
        )


class OpenAIResponsesImageAdapter:
    """Generate or edit an image through the OpenAI Responses image tool.

    The OpenAI SDK is imported lazily so the core runtime and tests stay
    dependency-free.
    """

    name = "openai-responses-image"

    def __init__(
        self,
        *,
        response_model: str | None = None,
        image_model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> None:
        self.response_model = response_model or os.getenv(
            "OPENAI_RESPONSE_MODEL", "gpt-5"
        )
        self.image_model = image_model or os.getenv(
            "OPENAI_IMAGE_MODEL", "gpt-image-1"
        )
        self.size = size or os.getenv("OPENAI_IMAGE_SIZE", "1024x1536")
        self.quality = quality or os.getenv("OPENAI_IMAGE_QUALITY", "high")

    @staticmethod
    def _data_url(path: Path) -> str:
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _item_value(item: object, key: str):
        if isinstance(item, dict):
            return item.get(key)
        return getattr(item, key, None)

    def generate(
        self, request: GenerationRequest, package: PromptPackage
    ) -> GenerationResult:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                'install the optional dependency with: pip install -e ".[openai]"'
            ) from exc

        content: list[dict[str, str]] = [
            {
                "type": "input_text",
                "text": (
                    f"{package.positive_prompt}\n\n负面约束：{package.negative_prompt}"
                    "\n\n必须调用图像生成工具并返回最终图片。"
                ),
            }
        ]
        if request.identity_reference:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._data_url(
                        request.identity_reference.resolve()
                    ),
                    "detail": "high",
                }
            )

        tool: dict[str, object] = {
            "type": "image_generation",
            "model": self.image_model,
            "action": "edit" if request.identity_reference else "generate",
            "size": self.size,
            "quality": self.quality,
            "output_format": "png",
        }
        if request.identity_reference:
            tool["input_fidelity"] = "high"

        client = OpenAI()
        response = client.responses.create(
            model=self.response_model,
            input=[{"role": "user", "content": content}],
            tools=[tool],
        )

        images: list[str] = []
        for item in response.output:
            if self._item_value(item, "type") == "image_generation_call":
                result = self._item_value(item, "result")
                if result:
                    images.append(result)
        if not images:
            raise RuntimeError(
                "OpenAI response did not contain an image_generation_call result"
            )

        request.output_dir.mkdir(parents=True, exist_ok=True)
        output = request.output_dir / f"{request.output_name}.png"
        output.write_bytes(base64.b64decode(images[0]))
        return GenerationResult(
            status="generated",
            adapter=self.name,
            output_path=output,
            metadata={
                "response_id": getattr(response, "id", None),
                "response_model": self.response_model,
                "image_model": self.image_model,
                "requested_aspect_ratio": request.aspect_ratio,
                "api_size": self.size,
            },
        )
