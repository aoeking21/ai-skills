from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import GenerationRequest, PromptPackage


ROUTE_ROW_RE = re.compile(
    r"^\|\s*`(?P<id>[^`]+)`\s*\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<category>[^|]+?)\s*\|\s*(?P<triggers>[^|]+?)\s*\|\s*\[[^]]+\]\((?P<path>[^)]+)\)\s*\|$",
    re.MULTILINE,
)
OVERLAY_ROW_RE = re.compile(
    r"^\|\s*`(?P<id>[^`]+)`\s*\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<triggers>[^|]+?)\s*\|\s*\[[^]]+\]\((?P<path>[^)]+)\)\s*\|$",
    re.MULTILINE,
)
SPLIT_TRIGGER_RE = re.compile(r"[、,，/]+")


@dataclass(frozen=True)
class RegistryEntry:
    item_id: str
    name: str
    triggers: tuple[str, ...]
    path: str


class PromptBuilder:
    """Build a deterministic prompt package from the Markdown Skill rules."""

    ROUTE_ALIASES = {
        "travel-vacation": ("海边", "海浪", "沙滩", "海岸", "度假", "海岛", "旅行"),
        "clean-lifestyle": ("生活方式", "生活照", "自然写真"),
        "sporty-active": ("运动", "网球", "跑步", "健身"),
    }
    OVERLAY_ALIASES = {
        "bright-heroine": ("明艳", "明媚", "女主感", "抓眼"),
        "cold-heroine": ("清冷", "疏离", "克制"),
        "intellectual": ("知性", "高智感", "书卷气"),
    }

    def __init__(self, skill_root: Path):
        self.skill_root = skill_root.resolve()
        self.skill_dir = self.skill_root / "skill"
        self.routes = self._load_registry(self.skill_dir / "style-registry.md", ROUTE_ROW_RE)
        self.overlays = self._load_registry(self.skill_dir / "overlay-registry.md", OVERLAY_ROW_RE)

    @staticmethod
    def _load_registry(path: Path, pattern: re.Pattern[str]) -> dict[str, RegistryEntry]:
        text = path.read_text(encoding="utf-8")
        entries: dict[str, RegistryEntry] = {}
        for match in pattern.finditer(text):
            triggers = tuple(
                item.strip().strip("`")
                for item in SPLIT_TRIGGER_RE.split(match.group("triggers"))
                if item.strip()
            )
            entry = RegistryEntry(
                item_id=match.group("id").strip(),
                name=match.group("name").strip(),
                triggers=triggers,
                path=match.group("path").strip(),
            )
            entries[entry.item_id] = entry
        if not entries:
            raise ValueError(f"no registry entries found in {path}")
        return entries

    @staticmethod
    def _request_text(request: GenerationRequest) -> str:
        return " ".join((request.task, *request.requirements)).lower()

    def _select_entry(
        self,
        request: GenerationRequest,
        entries: dict[str, RegistryEntry],
        explicit_id: str | None,
        aliases: dict[str, tuple[str, ...]],
        fallback: str | None,
    ) -> RegistryEntry | None:
        if explicit_id:
            if explicit_id not in entries:
                raise ValueError(f"unknown registry ID: {explicit_id}")
            return entries[explicit_id]

        text = self._request_text(request)
        scored: list[tuple[int, str, RegistryEntry]] = []
        for entry in entries.values():
            score = 0
            if entry.name.lower() in text:
                score += 100
            for trigger in entry.triggers:
                if trigger and trigger.lower() in text:
                    score += 10 + min(len(trigger), 8)
            for alias in aliases.get(entry.item_id, ()):
                if alias.lower() in text:
                    score += 25
            scored.append((score, entry.item_id, entry))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        if scored and scored[0][0] > 0:
            return scored[0][2]
        return entries.get(fallback) if fallback else None

    def build(self, request: GenerationRequest) -> PromptPackage:
        route = self._select_entry(
            request, self.routes, request.route_id, self.ROUTE_ALIASES, "clean-lifestyle"
        )
        if route is None:
            raise RuntimeError("unable to select a route")
        overlay = self._select_entry(
            request, self.overlays, request.overlay_id, self.OVERLAY_ALIASES, None
        )

        route_file = self.skill_dir / route.path
        if not route_file.is_file():
            raise FileNotFoundError(f"route file is missing: {route_file}")
        overlay_file = self.skill_dir / overlay.path if overlay else None
        if overlay_file and not overlay_file.is_file():
            raise FileNotFoundError(f"overlay file is missing: {overlay_file}")

        requirements = "；".join(request.requirements) or "未提供额外要求"
        identity_block = (
            "把上传照片标记为 identity_reference，作为唯一人物身份参考。严格保留真实脸型、"
            "眉眼结构、眼距、鼻唇结构、肤色、年龄感、自然不对称和整体可识别度；允许改变服装、"
            "姿态、场景、镜头、光线与滤镜。不得换脸、混脸、模板脸或年轻化。"
            if request.identity_reference
            else "人物必须是虚构且明确成年的东方女性，不使用现实第三方身份。"
        )
        overlay_text = (
            f"叠加气质 Overlay：{overlay.name}（{overlay.item_id}），只增强气质和主体存在感，"
            "不得覆盖主 Route 或用户锁定参数。"
            if overlay
            else "不叠加额外气质 Overlay。"
        )

        positive = "\n\n".join(
            [
                f"生成一张 {request.aspect_ratio} 竖版、完整全身、真实摄影质感的成年女性人像。"
                f"任务：{request.task}。明确要求：{requirements}。",
                identity_block,
                f"唯一主 Route：{route.name}（{route.item_id}）。{overlay_text}",
                "把画面组织成一个真实可拍摄的瞬间：确定一个明确时间切片、一个轻微主事件和连贯动作链；"
                "动作必须来自重心变化、肩颈、手部、衣料、发丝、头部方向与视线落点的自然联动。"
                "动态抓拍不得退化为模特站姿，不持续凝视镜头。场景只保留两到三个选择性环境细节。",
                "镜头必须完整保留头顶、双脚和动作相关环境，采用自然透视与可信景深。"
                "光线服务真实肤色、衣料材质与环境反光，形成明亮通透但不过曝的日系生活方式影调。"
                "服装必须完整覆盖重点部位；镂空设计只能作为优雅结构装饰，不得造成透明裸露。",
            ]
        )

        negatives = [
            "人物身份漂移、换脸、混脸、模板脸、网红脸、过度年轻化",
            "摆拍、僵硬站姿、持续凝视镜头、夸张模特动作、动作链不成立",
            "裁掉头顶或双脚、半身构图、比例失真、多余肢体、手脚变形",
            "透明服装、重点部位裸露、露骨性行为、未成年感或年龄模糊",
            "塑料皮肤、过度磨皮、重度 HDR、虚假海水、CG 感、插画感",
            *request.extra_negative,
        ]

        rules_loaded = [
            "SKILL.md",
            "skill/skill.md",
            "skill/style-registry.md",
            route_file.relative_to(self.skill_root).as_posix(),
            "skill/core/reference-image-lock.md" if request.identity_reference else "skill/core/safety-boundary.md",
            "skill/core/director-gate.md",
            "skill/core/parameter-lock.md",
            "skill/core/output-format.md",
            "skill/references/director-expansion.md",
            "skill/references/visual-libraries.md",
        ]
        if overlay_file:
            rules_loaded.extend(
                [
                    "skill/overlay-registry.md",
                    overlay_file.relative_to(self.skill_root).as_posix(),
                ]
            )

        return PromptPackage(
            positive_prompt=positive,
            negative_prompt="；".join(negatives),
            route_id=route.item_id,
            route_name=route.name,
            overlay_id=overlay.item_id if overlay else None,
            rules_loaded=rules_loaded,
            metadata={
                "aspect_ratio": request.aspect_ratio,
                "identity_reference": str(request.identity_reference) if request.identity_reference else None,
                "route_file": route_file.relative_to(self.skill_root).as_posix(),
                "overlay_file": overlay_file.relative_to(self.skill_root).as_posix() if overlay_file else None,
            },
        )
