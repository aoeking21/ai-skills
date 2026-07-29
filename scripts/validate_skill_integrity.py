#!/usr/bin/env python3
"""Validate repository-local Markdown links and female-portrait-director integrity.

Checks:
1. Every repository-local Markdown link that targets a ``.md`` file exists.
2. ``skill/style-registry.md`` and ``skill/routes/**/*.md`` are in one-to-one sync.
3. Every ``skill/core/**/*.md`` and ``skill/references/**/*.md`` dependency exists
   and is reachable from the Skill entrypoints.

The script uses only the Python standard library so it can run in GitHub Actions
without installing dependencies.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

MARKDOWN_INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_REFERENCE_DEF_RE = re.compile(
    r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE
)
HTML_HREF_RE = re.compile(r"\bhref\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")

ROUTE_ROW_RE = re.compile(
    r"^\|\s*`(?P<route_id>[^`]+)`\s*\|.*?\]\((?P<path>routes/[^)#?]+\.md)(?:[?#][^)]*)?\)",
    re.MULTILINE,
)
ROUTE_ID_RE = re.compile(
    r"(?im)^\s*route_id\s*[：:]\s*`?(?P<route_id>[A-Za-z0-9_-]+)`?\s*$"
)

# Path-like references frequently appear inside fenced dependency lists, so this
# extractor intentionally scans the original Markdown text rather than the
# fence-stripped text used by the ordinary Markdown-link checker.
SKILL_PATH_REFERENCE_RE = re.compile(
    r"(?<![\w./-])(?P<path>"
    r"(?:\.\./|\./)*"
    r"(?:skill/)?"
    r"(?:core|references|routes|tools|overlays)/"
    r"[^\s`'\"<>\]\[(){}]+?\.md"
    r"|skill/(?:skill|help|style-registry|tool-registry|overlay-registry|"
    r"parameter_schema|public_instructions|usage_examples)\.md"
    r")"
)

IGNORED_SCHEMES = {
    "http",
    "https",
    "mailto",
    "tel",
    "data",
    "javascript",
}


@dataclass(frozen=True)
class Finding:
    category: str
    source: Path
    line: int
    target: str
    message: str


@dataclass
class ValidationResult:
    markdown_files: int = 0
    markdown_links: int = 0
    registered_routes: int = 0
    actual_routes: int = 0
    core_reference_files: int = 0
    reachable_core_reference_files: int = 0
    findings: list[Finding] | None = None

    def __post_init__(self) -> None:
        if self.findings is None:
            self.findings = []

    @property
    def ok(self) -> bool:
        return not self.findings


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_fenced_code(text: str) -> str:
    """Remove fenced-code contents while preserving line numbers."""
    output: list[str] = []
    active_fence: str | None = None

    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        marker = match.group(1) if match else None

        if active_fence is None and marker:
            active_fence = marker[0] * len(marker)
            output.append("\n" if line.endswith("\n") else "")
            continue

        if active_fence is not None:
            if marker and marker[0] == active_fence[0] and len(marker) >= len(active_fence):
                active_fence = None
            output.append("\n" if line.endswith("\n") else "")
            continue

        output.append(line)

    return "".join(output)


def normalize_link_target(raw_target: str) -> str:
    target = html.unescape(raw_target.strip())
    if not target:
        return ""

    if target.startswith("<"):
        closing = target.find(">")
        if closing != -1:
            target = target[1:closing]
    else:
        # Markdown permits an optional title after whitespace. Local paths with
        # literal spaces should be percent-encoded or enclosed in angle brackets.
        target = target.split(maxsplit=1)[0]

    target = target.replace(r"\(", "(").replace(r"\)", ")")
    return target.strip()


def is_local_markdown_target(target: str) -> bool:
    if not target or target.startswith("#"):
        return False

    parsed = urlsplit(target)
    if parsed.scheme.lower() in IGNORED_SCHEMES or parsed.netloc:
        return False

    path = unquote(parsed.path)
    return path.lower().endswith(".md")


def resolve_repo_target(repo_root: Path, source: Path, target: str) -> Path:
    parsed = urlsplit(target)
    decoded_path = unquote(parsed.path)
    if decoded_path.startswith("/"):
        candidate = repo_root / decoded_path.lstrip("/")
    else:
        candidate = source.parent / decoded_path
    return candidate.resolve(strict=False)


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def extract_markdown_targets(text: str) -> list[tuple[str, int]]:
    stripped = strip_fenced_code(text)
    matches: list[tuple[str, int]] = []
    for regex in (MARKDOWN_INLINE_LINK_RE, MARKDOWN_REFERENCE_DEF_RE, HTML_HREF_RE):
        for match in regex.finditer(stripped):
            target = normalize_link_target(match.group(1))
            matches.append((target, line_number(stripped, match.start(1))))
    return matches


def validate_markdown_links(repo_root: Path, result: ValidationResult) -> None:
    markdown_files = sorted(
        path for path in repo_root.rglob("*.md") if ".git" not in path.parts
    )
    result.markdown_files = len(markdown_files)

    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for target, line in extract_markdown_targets(text):
            if not is_local_markdown_target(target):
                continue

            result.markdown_links += 1
            resolved = resolve_repo_target(repo_root, source, target)
            if not path_is_within(resolved, repo_root):
                result.findings.append(
                    Finding(
                        "markdown-link",
                        source,
                        line,
                        target,
                        "local Markdown link escapes the repository root",
                    )
                )
            elif not resolved.is_file():
                result.findings.append(
                    Finding(
                        "markdown-link",
                        source,
                        line,
                        target,
                        "target Markdown file does not exist",
                    )
                )


def parse_route_registry(registry: Path) -> dict[str, str]:
    text = registry.read_text(encoding="utf-8")
    routes: dict[str, str] = {}
    duplicate_ids: set[str] = set()

    for match in ROUTE_ROW_RE.finditer(text):
        route_id = match.group("route_id").strip()
        route_path = unquote(match.group("path").strip())
        if route_id in routes:
            duplicate_ids.add(route_id)
        routes[route_id] = route_path

    if duplicate_ids:
        joined = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"duplicate route IDs in registry: {joined}")
    return routes


def validate_routes(skill_root: Path, result: ValidationResult) -> None:
    registry = skill_root / "skill/style-registry.md"
    routes_root = skill_root / "skill/routes"

    if not registry.is_file():
        result.findings.append(
            Finding("route-registry", registry, 1, str(registry), "registry file is missing")
        )
        return
    if not routes_root.is_dir():
        result.findings.append(
            Finding("route-registry", routes_root, 1, str(routes_root), "routes directory is missing")
        )
        return

    try:
        registered = parse_route_registry(registry)
    except ValueError as exc:
        result.findings.append(
            Finding("route-registry", registry, 1, "route_id", str(exc))
        )
        registered = {}

    actual_paths = {
        path.relative_to(skill_root / "skill").as_posix()
        for path in routes_root.rglob("*.md")
    }
    registered_paths = set(registered.values())
    result.registered_routes = len(registered)
    result.actual_routes = len(actual_paths)

    for route_id, route_path in sorted(registered.items()):
        file_path = skill_root / "skill" / route_path
        if not file_path.is_file():
            result.findings.append(
                Finding(
                    "route-registry",
                    registry,
                    1,
                    route_path,
                    f"registered route '{route_id}' does not exist",
                )
            )
            continue

        route_text = file_path.read_text(encoding="utf-8")
        id_match = ROUTE_ID_RE.search(route_text)
        if not id_match:
            result.findings.append(
                Finding(
                    "route-registry",
                    file_path,
                    1,
                    route_id,
                    "route file does not declare route_id",
                )
            )
        elif id_match.group("route_id") != route_id:
            result.findings.append(
                Finding(
                    "route-registry",
                    file_path,
                    line_number(route_text, id_match.start()),
                    route_id,
                    f"route_id mismatch: file declares '{id_match.group('route_id')}'",
                )
            )

    for unregistered in sorted(actual_paths - registered_paths):
        result.findings.append(
            Finding(
                "route-registry",
                skill_root / "skill" / unregistered,
                1,
                unregistered,
                "route file exists but is not registered",
            )
        )


def resolve_skill_reference(skill_root: Path, source: Path, raw_path: str) -> Path:
    cleaned = unquote(raw_path).replace("\\", "/")
    if cleaned.startswith("skill/"):
        return (skill_root / cleaned).resolve(strict=False)
    return (source.parent / cleaned).resolve(strict=False)


def extract_skill_dependencies(skill_root: Path, source: Path, text: str) -> set[Path]:
    dependencies: set[Path] = set()

    for target, _ in extract_markdown_targets(text):
        if not is_local_markdown_target(target):
            continue
        resolved = resolve_repo_target(skill_root, source, target)
        if path_is_within(resolved, skill_root):
            dependencies.add(resolved)

    for match in SKILL_PATH_REFERENCE_RE.finditer(text):
        resolved = resolve_skill_reference(skill_root, source, match.group("path"))
        if path_is_within(resolved, skill_root):
            dependencies.add(resolved)

    return dependencies


def validate_dependency_closure(skill_root: Path, result: ValidationResult) -> None:
    all_skill_markdown = sorted(skill_root.rglob("*.md"))
    graph: dict[Path, set[Path]] = defaultdict(set)

    for source in all_skill_markdown:
        text = source.read_text(encoding="utf-8")
        for dependency in extract_skill_dependencies(skill_root, source, text):
            graph[source].add(dependency)

            relative = dependency.relative_to(skill_root).as_posix()
            if relative.startswith("skill/core/") or relative.startswith("skill/references/"):
                if not dependency.is_file():
                    result.findings.append(
                        Finding(
                            "dependency-closure",
                            source,
                            1,
                            relative,
                            "core/reference dependency does not exist",
                        )
                    )

    protected_files = {
        path.resolve()
        for directory in (skill_root / "skill/core", skill_root / "skill/references")
        if directory.is_dir()
        for path in directory.rglob("*.md")
    }
    result.core_reference_files = len(protected_files)

    entrypoints = [
        (skill_root / "SKILL.md").resolve(),
        (skill_root / "skill/skill.md").resolve(),
    ]
    missing_entrypoints = [entry for entry in entrypoints if not entry.is_file()]
    for missing in missing_entrypoints:
        result.findings.append(
            Finding(
                "dependency-closure",
                missing,
                1,
                missing.relative_to(skill_root).as_posix(),
                "Skill entrypoint is missing",
            )
        )

    reachable: set[Path] = set()
    queue: deque[Path] = deque(entry for entry in entrypoints if entry.is_file())
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        for dependency in graph.get(current, set()):
            if dependency.is_file() and dependency not in reachable:
                queue.append(dependency)

    reachable_protected = protected_files & reachable
    result.reachable_core_reference_files = len(reachable_protected)

    for orphan in sorted(protected_files - reachable_protected):
        result.findings.append(
            Finding(
                "dependency-closure",
                orphan,
                1,
                orphan.relative_to(skill_root).as_posix(),
                "core/reference file is not reachable from SKILL.md or skill/skill.md",
            )
        )


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def render_report(result: ValidationResult, repo_root: Path, skill_root: Path) -> str:
    status = "PASS" if result.ok else "FAIL"
    lines = [
        "# Skill integrity validation",
        "",
        f"**Status:** {status}",
        "",
        "## Scope",
        "",
        f"- Repository root: `{repo_root.as_posix()}`",
        f"- Skill root: `{display_path(skill_root, repo_root)}`",
        "",
        "## Checks",
        "",
        f"- Markdown files scanned: **{result.markdown_files}**",
        f"- Local `.md` links checked: **{result.markdown_links}**",
        f"- Registered routes: **{result.registered_routes}**",
        f"- Route files found: **{result.actual_routes}**",
        f"- Core/reference files: **{result.core_reference_files}**",
        f"- Reachable core/reference files: **{result.reachable_core_reference_files}**",
        "",
    ]

    if result.findings:
        lines.extend(["## Findings", ""])
        for finding in result.findings:
            source = display_path(finding.source, repo_root)
            lines.append(
                f"- **{finding.category}** `{source}:{finding.line}` → "
                f"`{finding.target}`: {finding.message}"
            )
    else:
        lines.extend(
            [
                "## Findings",
                "",
                "No broken Markdown links, route-registry drift, or core/reference closure errors were found.",
            ]
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument(
        "--skill-root",
        default="image-generation/female-portrait-director",
        help="female-portrait-director root relative to the repository",
    )
    parser.add_argument("--report", help="optional Markdown report output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    skill_root = (repo_root / args.skill_root).resolve()

    if not repo_root.is_dir():
        print(f"error: repository root does not exist: {repo_root}", file=sys.stderr)
        return 2
    if not skill_root.is_dir():
        print(f"error: skill root does not exist: {skill_root}", file=sys.stderr)
        return 2
    if not path_is_within(skill_root, repo_root):
        print("error: skill root must be inside repository root", file=sys.stderr)
        return 2

    result = ValidationResult()
    validate_markdown_links(repo_root, result)
    validate_routes(skill_root, result)
    validate_dependency_closure(skill_root, result)

    report = render_report(result, repo_root, skill_root)
    print(report, end="")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
