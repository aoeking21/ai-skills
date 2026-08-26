from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from female_portrait_director_runtime import (
    DryRunAdapter,
    GenerationPipeline,
    GenerationRequest,
    IdentityLockValidator,
    OpenAIImageAPIAdapter,
    OpenAIResponsesImageAdapter,
    PromptBuilder,
    validate_gpt_image_2_size,
)


def make_skill_root(base: Path) -> Path:
    root = base / "female-portrait-director"
    skill = root / "skill"
    (skill / "routes/lifestyle").mkdir(parents=True)
    (skill / "overlays").mkdir(parents=True)
    (skill / "core").mkdir(parents=True)
    (root / "SKILL.md").write_text("# Skill", encoding="utf-8")
    (skill / "skill.md").write_text("# Workflow", encoding="utf-8")
    (skill / "core/governance-override-v1.7.md").write_text("# Governance", encoding="utf-8")
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
            self.assertIn("完整全身景别", package.positive_prompt)
            self.assertEqual(package.metadata["composition_mode"], "recompose")
            self.assertTrue(package.metadata["route_applied"])

    def test_restoration_preserves_composition_and_source_light(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = make_skill_root(Path(temp_dir))
            request = GenerationRequest(task="原片4K无损修复，保持原构图和人物")
            package = PromptBuilder(skill_root).build(request)
            self.assertEqual(package.metadata["composition_mode"], "preserve")
            self.assertEqual(package.metadata["lighting_mode"], "preserve-source")
            self.assertFalse(package.metadata["route_applied"])
            self.assertIsNone(package.metadata["route_file"])
            self.assertIn("风格 Route：未启用", package.positive_prompt)
            self.assertIn("禁止为了美观重新摆姿", package.positive_prompt)

    def test_reference_beauty_edit_defaults_to_preserve(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = make_skill_root(Path(temp_dir))
            request = GenerationRequest(
                task="医美级美颜，保持人物本人",
                identity_reference=Path("reference.jpg"),
                identity_authorized=True,
            )
            package = PromptBuilder(skill_root).build(request)
            self.assertEqual(package.metadata["composition_mode"], "preserve")
            self.assertEqual(package.metadata["lighting_mode"], "preserve-source")
            self.assertEqual(package.metadata["beauty_mode"], "clinical-natural")

    def test_explicit_recompose_and_relight_override_reference_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = make_skill_root(Path(temp_dir))
            request = GenerationRequest(
                task="自动构图，伦勃朗重新打光，医美级美颜",
                identity_reference=Path("reference.jpg"),
                identity_authorized=True,
            )
            package = PromptBuilder(skill_root).build(request)
            self.assertEqual(package.metadata["composition_mode"], "recompose")
            self.assertEqual(package.metadata["lighting_mode"], "relight")
            self.assertEqual(package.metadata["beauty_mode"], "clinical-natural")

    def test_clinical_beauty_keeps_identity_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = make_skill_root(Path(temp_dir))
            request = GenerationRequest(task="自动完美构图，医美级美颜，完美光影")
            package = PromptBuilder(skill_root).build(request)
            self.assertEqual(package.metadata["beauty_mode"], "clinical-natural")
            self.assertIn("严格保留脸型、骨相、眼距、鼻唇结构", package.positive_prompt)


class AdapterContractTests(unittest.TestCase):
    def test_image_api_uses_exact_model_and_omits_input_fidelity(self) -> None:
        request = GenerationRequest(task="test", aspect_ratio="3:4")
        package = type("P", (), {"positive_prompt": "p", "negative_prompt": "n"})()
        params = OpenAIImageAPIAdapter().build_api_parameters(request, package)
        self.assertEqual(params["model"], "gpt-image-2")
        self.assertEqual(params["size"], "1152x1536")
        self.assertNotIn("input_fidelity", params)

    def test_responses_tool_does_not_claim_underlying_image_model(self) -> None:
        tool = OpenAIResponsesImageAdapter().build_tool_parameters(
            GenerationRequest(task="test")
        )
        self.assertEqual(tool["type"], "image_generation")
        self.assertNotIn("model", tool)
        self.assertNotIn("input_fidelity", tool)

    def test_size_contract_supports_4k_but_rejects_4096_edge(self) -> None:
        self.assertEqual(validate_gpt_image_2_size("2160x3840"), "2160x3840")
        with self.assertRaises(ValueError):
            validate_gpt_image_2_size("2304x4096")


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
                allowed_changes=("服装", "场景"),
                output_dir=temp / "outputs",
                output_name="test-generation",
            )
            result = GenerationPipeline(skill_root, DryRunAdapter()).run(request)
            self.assertEqual(result.status, "dry_run")
            self.assertTrue(result.output_path and result.output_path.is_file())
            self.assertTrue(result.manifest_path and result.manifest_path.is_file())
            self.assertEqual(result.metadata["selected_route"], "travel-vacation")
            self.assertEqual(result.metadata["selected_overlay"], "bright-heroine")
            self.assertIn(result.metadata["composition_mode"], {"preserve", "recompose"})


if __name__ == "__main__":
    unittest.main()
