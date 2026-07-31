#!/usr/bin/env python3
"""Validate canonical Agent Skills stored under skills/*/."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: unterminated YAML frontmatter") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def validate_links(skill_root: Path) -> list[str]:
    errors: list[str] = []
    for source in skill_root.rglob("*.md"):
        text = source.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = raw.strip().split(maxsplit=1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):
                continue
            candidate = (source.parent / unquote(parsed.path)).resolve()
            try:
                candidate.relative_to(skill_root.resolve())
            except ValueError:
                errors.append(f"{source}: local link escapes skill: {target}")
                continue
            if not candidate.exists():
                errors.append(f"{source}: missing local link target: {target}")
    return errors


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skills_root = repo_root / "skills"
    errors: list[str] = []
    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    if not skill_files:
        errors.append("no canonical skills found under skills/*/SKILL.md")
    for skill_file in skill_files:
        root = skill_file.parent
        try:
            metadata = parse_frontmatter(skill_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if not name or not description:
            errors.append(f"{skill_file}: name and description are required")
        if name != root.name:
            errors.append(f"{skill_file}: name must match directory {root.name}")
        if name and not NAME_RE.fullmatch(name):
            errors.append(f"{skill_file}: invalid skill name {name!r}")
        if len(description) > 1024:
            errors.append(f"{skill_file}: description exceeds 1024 characters")
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            errors.append(f"{root}: manifest.json is missing")
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("name") != name:
                errors.append(f"{manifest_path}: name mismatch")
            for relative in manifest.get("files", []):
                if not (root / relative).is_file():
                    errors.append(f"{manifest_path}: missing listed file {relative}")
        errors.extend(validate_links(root))
    if errors:
        print("Agent Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(skill_files)} canonical Agent Skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
