from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from female_portrait_director_runtime import (
    DryRunAdapter,
    GenerationPipeline,
    GenerationRequest,
    IdentityLockValidator,
    PromptBuilder,
)


def make_skill_root(base: Path) -> Path:
    root = base / "female-portrait-director"
    skill = root / "skill"
    (skill / "routes/lifestyle").mkdir(parents=True)
    (skill / "overlays").mkdir(parents=True)
    (root / "SKILL.md").write_text("# Skill", encoding="utf-8")
    (skill / "skill.md").write_text("# Workflow", encoding="utf-8")
    (skill / "style-registry.md").write_text(
        """# Routes
| Route ID | 风格 | 分类 | 主要触发词 | 文件 |
| --- | --- | --- | --- | --- |
| `clean-lifestyle` | 清纯生活照 | lifestyle | 清纯、自然、生活照 | [route](routes/lifestyle/clean-lifestyle.md) |
| `travel-vacation` | 旅行假日写真 | lifestyle | 旅行、假日、度假、海岛 | [route](routes/lifestyle/travel-vacation.md) |
""",
        encoding="utf-8",
    )
    (skill / "overlay-registry.md").write_text(
        """# Overlays
| Overlay ID | 气质方向 | 主要触发词 | 文件 |
| --- | --- | --- | --- |
| `bright-heroine` | 明艳女主增强 | 明艳、明媚、女主感 | [overlay](overlays/bright-heroine.md) |
""",
        encoding="utf-8",
    )
    (skill / "routes/lifestyle/clean-lifestyle.md").write_text(
        "route_id: clean-lifestyle", encoding="utf-8"
    )
    (skill / "routes/lifestyle/travel-vacation.md").write_text(
        "route_id: travel-vacation", encoding="utf-8"
    )
    (skill / "overlays/bright-heroine.md").write_text(
        "overlay_id: bright-heroine", encoding="utf-8"
    )
    return root


class PromptBuilderTests(unittest.TestCase):
    def test_selects_travel_route_and_bright_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = make_skill_root(Path(temp_dir))
            request = GenerationRequest(
                task="海边日系明艳生活方式摄影",
                requirements=("9:16", "全身", "动态抓拍", "真实摄影"),
            )
            package = PromptBuilder(skill_root).build(request)
            self.assertEqual(package.route_id, "travel-vacation")
            self.assertEqual(package.overlay_id, "bright-heroine")
            self.assertIn("9:16", package.positive_prompt)
            self.assertIn("动态抓拍", package.positive_prompt)


class IdentityLockTests(unittest.TestCase):
    def test_requires_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reference = Path(temp_dir) / "reference.jpg"
            reference.write_bytes(b"fake-image")
            request = GenerationRequest(
                task="test",
                identity_reference=reference,
                identity_authorized=False,
            )
            with self.assertRaises(ValueError):
                IdentityLockValidator().preflight(request)


class PipelineTests(unittest.TestCase):
    def test_dry_run_writes_prompt_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            skill_root = make_skill_root(temp)
            reference = temp / "reference.jpg"
            reference.write_bytes(b"fake-image")
            request = GenerationRequest(
                task="海边日系明艳生活方式摄影",
                requirements=(
                    "9:16",
                    "完整全身",
                    "动态抓拍",
                    "真实摄影",
                    "人物身份锁定",
                ),
                identity_reference=reference,
                identity_authorized=True,
                output_dir=temp / "outputs",
                output_name="test-generation",
            )
            result = GenerationPipeline(skill_root, DryRunAdapter()).run(request)
            self.assertEqual(result.status, "dry_run")
            self.assertTrue(result.output_path and result.output_path.is_file())
            self.assertTrue(result.manifest_path and result.manifest_path.is_file())
            self.assertEqual(result.metadata["selected_route"], "travel-vacation")
            self.assertEqual(result.metadata["selected_overlay"], "bright-heroine")


if __name__ == "__main__":
    unittest.main()
