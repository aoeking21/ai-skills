from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Protocol

from .models import GenerationRequest, GenerationResult, PromptPackage


SIZE_RE = re.compile(r"^(?P<w>\d+)x(?P<h>\d+)$")
DEFAULT_SIZE_BY_RATIO = {
    "1:1": "1024x1024",
    "2:3": "1024x1536",
    "3:4": "1152x1536",
    "4:5": "1280x1600",
    "9:16": "1152x2048",
    "16:9": "2048x1152",
}


def validate_gpt_image_2_size(size: str) -> str:
    if size == "auto":
        return size
    match = SIZE_RE.fullmatch(size)
    if not match:
        raise ValueError(f"invalid GPT Image 2 size: {size}")
    width = int(match.group("w"))
    height = int(match.group("h"))
    long_edge = max(width, height)
    short_edge = min(width, height)
    pixels = width * height
    if long_edge > 3840:
        raise ValueError("GPT Image 2 maximum edge is 3840px")
    if width % 16 or height % 16:
        raise ValueError("GPT Image 2 width and height must be multiples of 16")
    if long_edge / short_edge > 3:
        raise ValueError("GPT Image 2 long-edge to short-edge ratio must not exceed 3:1")
    if not 655_360 <= pixels <= 8_294_400:
        raise ValueError("GPT Image 2 total pixels must be between 655,360 and 8,294,400")
    return size


def resolve_gpt_image_2_size(request: GenerationRequest, fallback: str | None = None) -> str:
    size = request.output_size or fallback or DEFAULT_SIZE_BY_RATIO.get(request.aspect_ratio, "auto")
    return validate_gpt_image_2_size(size)


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


class OpenAIImageAPIAdapter:
    """Generate or edit a single image through the Image API with exact GPT Image model selection."""

    name = "openai-image-api"

    def __init__(
        self,
        *,
        image_model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> None:
        self.image_model = image_model or os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
        self.size = size or os.getenv("OPENAI_IMAGE_SIZE")
        self.quality = quality or os.getenv("OPENAI_IMAGE_QUALITY", "high")

    def build_api_parameters(
        self, request: GenerationRequest, package: PromptPackage
    ) -> dict[str, object]:
        params: dict[str, object] = {
            "model": self.image_model,
            "prompt": f"{package.positive_prompt}\n\n负面约束：{package.negative_prompt}",
            "size": resolve_gpt_image_2_size(request, self.size),
            "quality": self.quality,
            "output_format": "png",
            "background": "auto",
            "n": 1,
        }
        return params

    @staticmethod
    def _error_details(exc: Exception) -> tuple[str | None, str | None, int | None]:
        error = getattr(exc, "error", None)
        code = getattr(error, "code", None) if error is not None else None
        error_type = getattr(error, "type", None) if error is not None else None
        status = getattr(exc, "status_code", None)
        if isinstance(error, dict):
            code = error.get("code", code)
            error_type = error.get("type", error_type)
        return code, error_type, status

    @classmethod
    def _raise_normalized_error(cls, exc: Exception) -> None:
        code, error_type, status = cls._error_details(exc)
        request_id = getattr(exc, "request_id", None)
        if error_type == "image_generation_user_error":
            raise RuntimeError(
                f"non-retryable image_generation_user_error code={code!r} request_id={request_id!r}; "
                "modify the prompt or input image before retrying"
            ) from exc
        if status == 429 or (isinstance(status, int) and status >= 500):
            raise RuntimeError(
                f"transient OpenAI image API failure status={status} request_id={request_id!r}; "
                "caller may retry with bounded backoff"
            ) from exc
        raise RuntimeError(
            f"OpenAI image API failure code={code!r} status={status!r} request_id={request_id!r}"
        ) from exc

    def generate(
        self, request: GenerationRequest, package: PromptPackage
    ) -> GenerationResult:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                'install the optional dependency with: pip install -e ".[openai]"'
            ) from exc

        client = OpenAI()
        params = self.build_api_parameters(request, package)
        operation = "edit" if request.identity_reference else "generate"
        try:
            if request.identity_reference:
                with request.identity_reference.resolve().open("rb") as reference:
                    result = client.images.edit(image=reference, **params)
            else:
                result = client.images.generate(**params)
        except Exception as exc:
            self._raise_normalized_error(exc)
            raise AssertionError("unreachable")

        if not getattr(result, "data", None) or not result.data[0].b64_json:
            raise RuntimeError("OpenAI Image API did not return base64 image data")

        request.output_dir.mkdir(parents=True, exist_ok=True)
        output = request.output_dir / f"{request.output_name}.png"
        output.write_bytes(base64.b64decode(result.data[0].b64_json))
        return GenerationResult(
            status="generated",
            adapter=self.name,
            output_path=output,
            metadata={
                "image_model": self.image_model,
                "operation": operation,
                "api_size": params["size"],
                "quality": self.quality,
            },
        )


class OpenAIResponsesImageAdapter:
    """Generate or edit through the Responses image-generation tool.

    Use this adapter for conversational or multi-turn workflows. The Responses
    image-generation tool chooses its own GPT Image model; exact gpt-image-2
    selection belongs to OpenAIImageAPIAdapter.
    """

    name = "openai-responses-image"

    def __init__(
        self,
        *,
        response_model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> None:
        self.response_model = response_model or os.getenv("OPENAI_RESPONSE_MODEL", "gpt-5.6")
        self.size = size or os.getenv("OPENAI_IMAGE_SIZE")
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

    def build_tool_parameters(self, request: GenerationRequest) -> dict[str, object]:
        tool: dict[str, object] = {
            "type": "image_generation",
            "action": "edit" if request.identity_reference else "generate",
            "quality": self.quality,
            "output_format": "png",
        }
        size = resolve_gpt_image_2_size(request, self.size)
        if size != "auto":
            tool["size"] = size
        return tool

    def generate(
        self, request: GenerationRequest, package: PromptPackage
    ) -> GenerationResult:
        try:
            from openai import OpenAI
        except ImportError as exc:
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
                    "image_url": self._data_url(request.identity_reference.resolve()),
                    "detail": "auto",
                }
            )

        client = OpenAI()
        response = client.responses.create(
            model=self.response_model,
            input=[{"role": "user", "content": content}],
            tools=[self.build_tool_parameters(request)],
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
                "image_model_selection": "responses-tool-managed",
                "requested_aspect_ratio": request.aspect_ratio,
                "api_size": resolve_gpt_image_2_size(request, self.size),
            },
        )
