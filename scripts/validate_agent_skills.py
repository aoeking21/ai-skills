#!/usr/bin/env python3
"""Validate canonical Agent Skills and repository-wide Skill governance.

Checks:
1. Canonical skills under skills/* have valid names, manifests and local links.
2. manifest.json name/version agree with SKILL.md frontmatter metadata.
3. Every SKILL.md in the repository participates in a unique-name policy.
4. Known distribution mirrors may share a name only with their declared canonical source.
5. The full female-portrait distribution mirror has the expected published file inventory.
6. Critical mirror entry and governance files remain semantically identical.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
METADATA_VERSION_RE = re.compile(r"(?m)^\s{2}version:\s*[\"']?([^\"'\s]+)")

ALLOWED_DUPLICATE_GROUPS = {
    "female-portrait-director": {
        "image-generation/female-portrait-director/SKILL.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/SKILL.md",
    }
}

# These files are internal workflow documents named ``SKILL.md`` inside the
# female-portrait bundle. They are not installable Agent Skill entrypoints and
# intentionally have no YAML frontmatter.
NON_AGENT_SKILL_DOCS = {
    "image-generation/female-portrait-director/skill/SKILL.md",
    "image-generation/female-portrait-director/skills/female-portrait-director/skill/SKILL.md",
}

FEMALE_CANONICAL_ROOT = "image-generation/female-portrait-director"
FEMALE_MIRROR_ROOT = "image-generation/female-portrait-director/skills/female-portrait-director"
FEMALE_PUBLISHED_PATHS = (
    "SKILL.md",
    "agents",
    "docs/prompt_safety.md",
    "docs/versioning.md",
    "examples",
    "skill",
)

MIRROR_ENTRY_PAIRS = [
    (
        "image-generation/female-portrait-director/SKILL.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/SKILL.md",
    ),
    (
        "image-generation/female-portrait-director/agents/openai.yaml",
        "image-generation/female-portrait-director/skills/female-portrait-director/agents/openai.yaml",
    ),
    (
        "image-generation/female-portrait-director/docs/versioning.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/docs/versioning.md",
    ),
    (
        "image-generation/female-portrait-director/skill/help.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/help.md",
    ),
    (
        "image-generation/female-portrait-director/skill/core/governance-override-v1.7.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/core/governance-override-v1.7.md",
    ),
    (
        "image-generation/female-portrait-director/skill/core/reference-image-lock.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/core/reference-image-lock.md",
    ),
    (
        "image-generation/female-portrait-director/skill/core/safety-boundary.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/core/safety-boundary.md",
    ),
    (
        "image-generation/female-portrait-director/skill/style-registry.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/style-registry.md",
    ),
    (
        "image-generation/female-portrait-director/skill/parameter_schema.md",
        "image-generation/female-portrait-director/skills/female-portrait-director/skill/parameter_schema.md",
    ),
]


def frontmatter_text(path: Path) -> str:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: unterminated YAML frontmatter") from exc
    return "\n".join(lines[1:end])


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = frontmatter_text(path)
    data: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def parse_metadata_version(path: Path) -> str | None:
    match = METADATA_VERSION_RE.search(frontmatter_text(path))
    return match.group(1) if match else None


def validate_links(skill_root: Path) -> list[str]:
    errors: list[str] = []
    for source in skill_root.rglob("*.md"):
        text = source.read_text(encoding="utf-8-sig")
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


def normalize_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip() + "\n"


def validate_repository_skill_names(repo_root: Path) -> list[str]:
    errors: list[str] = []
    locations: dict[str, set[str]] = defaultdict(set)

    for skill_file in sorted(repo_root.rglob("SKILL.md")):
        if ".git" in skill_file.parts:
            continue
        relative = skill_file.relative_to(repo_root).as_posix()
        if relative in NON_AGENT_SKILL_DOCS:
            continue
        try:
            metadata = parse_frontmatter(skill_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        name = metadata.get("name", "")
        if not name:
            errors.append(f"{skill_file}: name is required")
            continue
        locations[name].add(relative)

    for name, paths in sorted(locations.items()):
        if len(paths) <= 1:
            continue
        allowed = ALLOWED_DUPLICATE_GROUPS.get(name)
        if allowed is None or paths != allowed:
            errors.append(
                f"duplicate Skill name {name!r}: " + ", ".join(sorted(paths))
            )

    return errors


def _published_files(root: Path, published_paths: tuple[str, ...]) -> set[str]:
    files: set[str] = set()
    for relative in published_paths:
        target = root / relative
        if target.is_file():
            files.add(target.relative_to(root).as_posix())
        elif target.is_dir():
            files.update(
                path.relative_to(root).as_posix()
                for path in target.rglob("*")
                if path.is_file()
            )
        else:
            files.add(f"__MISSING__/{relative}")
    return files


def validate_mirror_inventory(repo_root: Path) -> list[str]:
    errors: list[str] = []
    canonical = repo_root / FEMALE_CANONICAL_ROOT
    mirror = repo_root / FEMALE_MIRROR_ROOT
    expected = _published_files(canonical, FEMALE_PUBLISHED_PATHS)
    actual = {
        path.relative_to(mirror).as_posix()
        for path in mirror.rglob("*")
        if path.is_file()
    }
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append("female distribution mirror missing files: " + ", ".join(missing))
    if extra:
        errors.append("female distribution mirror has unexpected files: " + ", ".join(extra))
    return errors


def validate_mirror_entrypoints(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for canonical_rel, mirror_rel in MIRROR_ENTRY_PAIRS:
        canonical = repo_root / canonical_rel
        mirror = repo_root / mirror_rel
        if not canonical.is_file():
            errors.append(f"missing canonical mirror source: {canonical_rel}")
            continue
        if not mirror.is_file():
            errors.append(f"missing distribution mirror entry: {mirror_rel}")
            continue
        if normalize_text(canonical) != normalize_text(mirror):
            errors.append(
                f"distribution mirror drift: {mirror_rel} differs from {canonical_rel}"
            )
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
        skill_version = parse_metadata_version(skill_file)

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
            manifest_version = manifest.get("version")
            if skill_version and manifest_version != skill_version:
                errors.append(
                    f"{manifest_path}: version {manifest_version!r} does not match "
                    f"SKILL.md metadata.version {skill_version!r}"
                )
            for relative in manifest.get("files", []):
                if not (root / relative).is_file():
                    errors.append(f"{manifest_path}: missing listed file {relative}")

        errors.extend(validate_links(root))

    errors.extend(validate_repository_skill_names(repo_root))
    errors.extend(validate_mirror_inventory(repo_root))
    errors.extend(validate_mirror_entrypoints(repo_root))

    if errors:
        print("Agent Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validated {len(skill_files)} canonical Agent Skill(s); "
        "repository-wide name, version, inventory and mirror governance passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
