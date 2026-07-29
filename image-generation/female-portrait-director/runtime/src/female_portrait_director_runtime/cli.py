from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import DryRunAdapter, OpenAIResponsesImageAdapter
from .models import GenerationRequest
from .pipeline import GenerationPipeline


def default_skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the female-portrait-director generation pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser(
        "generate", help="build a prompt package and optionally generate an image"
    )
    generate.add_argument("--request", type=Path, required=True, help="JSON request file")
    generate.add_argument(
        "--adapter", choices=("dry-run", "openai"), default="dry-run"
    )
    generate.add_argument("--skill-root", type=Path, default=default_skill_root())
    return parser


def main() -> int:
    args = build_parser().parse_args()
    data = json.loads(args.request.read_text(encoding="utf-8"))
    request = GenerationRequest.from_mapping(data)
    if request.identity_reference and not request.identity_reference.is_absolute():
        request.identity_reference = (
            args.request.parent / request.identity_reference
        ).resolve()
    if not request.output_dir.is_absolute():
        request.output_dir = (args.request.parent / request.output_dir).resolve()

    adapter = (
        DryRunAdapter()
        if args.adapter == "dry-run"
        else OpenAIResponsesImageAdapter()
    )
    result = GenerationPipeline(args.skill_root, adapter).run(request)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
