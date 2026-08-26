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
    RESTORATION_TERMS = ("4k", "无损修复", "原片修复", "修复原图", "照片修复", "超分", "清晰度修复")
    RECOMPOSE_TERMS = ("自动构图", "重新构图", "重构构图", "换构图", "改构图", "重新设计构图")
    RELIGHT_TERMS = ("伦勃朗", "rembrandt", "重新打光", "重打光", "影棚光", "蝴蝶光", "重新设计光影")
    CLINICAL_BEAUTY_TERMS = ("医美级", "医美美颜", "医美级美颜", "高级精修", "大师精修")
    FULL_BODY_TERMS = ("完整全身", "全身", "头到脚")
    HALF_BODY_TERMS = ("半身", "上半身", "胸部以上", "腰部以上")
    CLOSEUP_TERMS = ("近景", "特写", "头像", "大头照")

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

    @staticmethod
    def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
        return any(term.lower() in text for term in terms)

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

    def _resolve_composition_mode(self, request: GenerationRequest, text: str) -> str:
        if request.composition_mode != "auto":
            return request.composition_mode
        if self._contains_any(text, self.RECOMPOSE_TERMS):
            return "recompose"
        if self._contains_any(text, self.RESTORATION_TERMS):
            return "preserve"
        return "recompose"

    def _resolve_lighting_mode(self, request: GenerationRequest, text: str) -> str:
        if request.lighting_mode != "auto":
            return request.lighting_mode
        if self._contains_any(text, self.RESTORATION_TERMS):
            return "preserve-source"
        if self._contains_any(text, self.RELIGHT_TERMS):
            return "relight"
        return "relight"

    def _resolve_beauty_mode(self, request: GenerationRequest, text: str) -> str:
        if request.beauty_mode != "natural":
            return request.beauty_mode
        if self._contains_any(text, self.CLINICAL_BEAUTY_TERMS):
            return "clinical-natural"
        return request.beauty_mode

    def _framing_instruction(self, text: str) -> str:
        if self._contains_any(text, self.FULL_BODY_TERMS):
            return "使用完整全身景别，头顶、双手与双脚均须完整保留。"
        if self._contains_any(text, self.HALF_BODY_TERMS):
            return "使用用户要求的半身或上半身景别，避免机械裁切关节和下巴。"
        if self._contains_any(text, self.CLOSEUP_TERMS):
            return "使用近景或特写景别，保留完整头发、下巴和自然视线空间。"
        return "景别由任务和源图共同决定，不强制全身、半身或特写。"

    @staticmethod
    def _beauty_instruction(mode: str) -> str:
        if mode == "off":
            return "不执行额外美颜，只做任务必需的成像修复。"
        if mode == "clinical-natural":
            return (
                "执行医美级自然精修：改善临时瑕疵、肤色不均、眼下疲态和不自然反光，"
                "优化眉睫、唇纹与发丝边缘；严格保留脸型、骨相、眼距、鼻唇结构、年龄结构、"
                "面痣、毛孔和真实皮肤差异，禁止网红模板脸、塑料皮、过度年轻化和五官重塑。"
            )
        return (
            "执行自然精修：控制肤色、局部瑕疵和反射，保留毛孔、细纹、面痣、年龄感与真实皮肤纹理。"
        )

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

        text = self._request_text(request)
        composition_mode = self._resolve_composition_mode(request, text)
        lighting_mode = self._resolve_lighting_mode(request, text)
        beauty_mode = self._resolve_beauty_mode(request, text)
        requirements = "；".join(request.requirements) or "未提供额外要求"
        allowed_changes = "、".join(request.allowed_changes)

        if request.identity_reference:
            change_clause = (
                f"明确允许改变：{allowed_changes}。除此之外，源图中的人物身份与未授权元素保持不变。"
                if allowed_changes
                else "只改变完成本任务明确要求所必需的摄影变量；未明确授权改变的源图元素保持不变。"
            )
            identity_block = (
                "把上传照片标记为 identity_reference，作为唯一人物身份参考。严格保留真实脸型、"
                "眉眼结构、眼距、鼻唇结构、肤色、年龄感、自然不对称、面痣、纹身、眼镜及整体可识别度。"
                f"{change_clause} 禁止换脸、混脸、模板脸和身份漂移。"
            )
        else:
            identity_block = "人物必须是虚构且明确成年的女性，不宣称锁定任何现实第三方身份。"

        if composition_mode == "preserve":
            composition_block = (
                "构图模式 preserve：严格保持源图主体位置、视角、姿态、镜头关系和主要场景关系。"
                "画幅变化只允许安全裁切或扩展可推断背景，禁止为了美观重新摆姿、换机位或重建身体。"
            )
        else:
            composition_block = (
                "构图模式 recompose：在不改变身份和人体结构的前提下，自动优化主体位置、留白、"
                "视线空间、肩线、前中后景和裁切点；优先扩展背景而非切掉头发、手、脚或动作关键部位。"
            )

        if lighting_mode == "preserve-source":
            lighting_block = (
                "光影模式 preserve-source：保留源图主光方向、环境光逻辑和现场时间感，只优化曝光、"
                "动态范围、局部补光、白平衡与反差，禁止把现场照片擅自重建成另一套影棚灯位。"
            )
        else:
            lighting_block = (
                "光影模式 relight：允许按任务重新设计可信主光、辅光、负补光和必要的轮廓分离；"
                "所有灯位必须符合单一曝光与真实空间关系，暗部保持可读，肤色和材质不得被色偏污染。"
            )

        overlay_text = (
            f"叠加气质 Overlay：{overlay.name}（{overlay.item_id}），只增强兼容的气质与主体存在感，"
            "不得覆盖用户锁定参数、人物身份、构图模式或光影模式。"
            if overlay
            else "不叠加额外气质 Overlay。"
        )

        positive = "\n\n".join(
            [
                f"生成一张 {request.aspect_ratio} 的真实摄影质感成年人物图像。任务：{request.task}。"
                f"明确要求：{requirements}。",
                identity_block,
                f"唯一主 Route：{route.name}（{route.item_id}）。{overlay_text}",
                f"{composition_block} {self._framing_instruction(text)}",
                lighting_block,
                self._beauty_instruction(beauty_mode),
                "若任务属于纪实、旅行、街头或动态场景，把画面组织成一个真实可拍摄的时间切片；"
                "动作来自重心、肩颈、手部、衣料、发丝、头部方向与视线的自然联动。"
                "若任务属于原片修复，则不得为了制造事件而改写原有动作和表情。",
            ]
        )

        negatives = [
            "人物身份漂移、换脸、混脸、模板脸、网红脸、无依据年轻化",
            "人体比例失真、多余肢体、手脚变形、无依据重构身体",
            "塑料皮肤、过度磨皮、毛孔夸张、重度 HDR、虚假锐化、CG 感、插画感",
            "违反已解析的构图模式、光影模式或用户锁定参数",
            "未成年感或年龄模糊",
            *request.extra_negative,
        ]

        rules_loaded = [
            "SKILL.md",
            "skill/skill.md",
            "skill/core/governance-override-v1.7.md",
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
                "output_size": request.output_size,
                "identity_reference": str(request.identity_reference) if request.identity_reference else None,
                "composition_mode": composition_mode,
                "lighting_mode": lighting_mode,
                "beauty_mode": beauty_mode,
                "allowed_changes": list(request.allowed_changes),
                "route_file": route_file.relative_to(self.skill_root).as_posix(),
                "overlay_file": overlay_file.relative_to(self.skill_root).as_posix() if overlay_file else None,
            },
        )
