# aoeking-xiezhen-director

面向授权成年人物长期写真、参考图编辑、原片修复和连续摄影项目的 Agent Skill。重点解决人物身份漂移、身体比例漂移、摆拍感、事件缺失、构图/光影模式冲突、过度美颜、衣料和环境物理失真，以及多张变体高度重复的问题。

当前版本：`1.4.0`。

## V1.4 核心升级

新增四份强制合同：

- `references/global-priority-contract.md`：统一用户本轮要求、身份不变量、长期 Profile、摄影物理、风格模块优先级。
- `references/beauty-retouch-contract.md`：将“医美级美颜”规范为身份安全的“医美级自然精修”。
- `references/composition-lighting-contract.md`：将构图拆成 `preserve / recompose`，光影拆成 `preserve-source / relight`。
- `references/batch-and-asset-routing-contract.md`：统一单张/多张和视觉参考图角色，防止历史成片污染人物真值。

原则：用户明确修改的可变字段必须生效；身份保留任务中未被用户要求改变的身份结构继续锁定；风格、美颜和灯光不能静默覆盖上游合同。

## 安装到 Codex

```bash
npx skills add aoeking21/ai-skills --skill aoeking-xiezhen-director -g -a codex -y
```

也可以从目录安装：

```bash
npx skills add https://github.com/aoeking21/ai-skills/tree/main/skills/aoeking-xiezhen-director -g -a codex -y
```

查看仓库中可安装的 Skills：

```bash
npx skills add aoeking21/ai-skills --list
```

临时调用：

```bash
npx skills use aoeking21/ai-skills --skill aoeking-xiezhen-director --agent codex
```

## 基础调用

```text
使用 $aoeking-xiezhen-director。
以上传照片中的授权成年女性为唯一身份参考。
生成长沙盛夏强风街头纪实。
自动优化构图，医美级自然精修，真实摄影光影，3:4。
```

系统会先确定任务模式、参考图角色、身份不变量、允许修改项、摄影事件、构图/光影模式，再编译最终 Prompt。

## 原片修复

```text
使用 $aoeking-xiezhen-director。
对上传照片做 4K 原片修复。
严格保持同一人物、原场景和原主光方向。
自动优化构图边界和曝光，医美级自然精修，保留毛孔、面痣和真实年龄。
```

该任务默认：

```text
mode: restoration
composition: preserve
lighting: preserve-source
beauty: clinical-natural
```

## 允许重构的写真

```text
使用 $aoeking-xiezhen-director。
以上传授权人物为唯一身份来源。
重新设计 3:4 高级棚拍构图，允许重新打光，使用克制伦勃朗侧光，深炭灰背景。
```

该任务可以使用：

```text
composition: recompose
lighting: relight
```

具体灯光策略仍服从人物身份、摄影物理和用户锁定项。

## GPT Image 2 专用 Adapter

Skill 内置 [`adapters/gpt-image-2.md`](adapters/gpt-image-2.md)，已于 2026-08-27 依据 OpenAI 官方 GPT Image 2 文档重新校准。

当前关键接口事实：

- 模型：`gpt-image-2`，可锁定 `gpt-image-2-2026-04-21`。
- 新图：`POST /v1/images/generations`。
- 参考图编辑：`POST /v1/images/edits`。
- GPT Image 2 的输入图始终高保真处理，编辑请求省略 `input_fidelity`。
- 当前不支持透明背景，使用 `auto` 或 `opaque`。
- 输出支持 PNG、JPEG、WebP。
- 支持大量自定义分辨率，只要满足尺寸约束。
- 官方列出的常用 4K 尺寸包括 `2160x3840` 和 `3840x2160`。

常用写真映射：

| 比例 | 推荐尺寸 |
|---|---:|
| 1:1 | `1024x1024` |
| 2:3 | `1024x1536` |
| 3:4 | `1152x1536` |
| 4:5 | `1280x1600` |
| 9:16 | `1152x2048` |
| 16:9 | `2048x1152` |
| 4K 9:16 | `2160x3840` |
| 4K 16:9 | `3840x2160` |

如果任务要求长边 `4096`，GPT Image 2 原生最大边当前是 `3840`。正确链路是先生成最大合规尺寸，再进入独立超分辨率后处理，不能直接向 API 提交 4096 边长。

## 多张独立图片

```text
使用 $aoeking-xiezhen-director 和 GPT Image 2 Adapter。
基于上传的授权成年人物参考图，生成五张同系列独立街头纪实人像。
五张使用不同摄影事件、动作阶段、重心、视线和机位。
```

默认每张形成独立 Event Card、完整 Prompt 和独立调用。用户明确要求独立照片时，不压成五宫格或拼图。

## GPT Image 2 街头纪实 V1.3

Skill 内置 [`presets/gpt-image-2-street-documentary-v1.3.md`](presets/gpt-image-2-street-documentary-v1.3.md)。该预设降低服装和空泛美化词权重，提高人物身份、摄影事件、动作物理和真实快门感。

适合：强风、雨后、街口避让、电动车气流、跨积水、旅行抓拍等具有现场因果的动态人像。

## 视觉参考图角色

参考图进入工作流前应声明用途：

```text
identity_anchor
body_anchor
unique_feature_anchor
style_reference
lighting_reference
scene_reference
wardrobe_reference
historical_output
failure_case
```

历史成片和其中附带的 Prompt 默认属于 `historical_output`，不会自动升级为人物真值或全局规则。

## 失败诊断与重试

失败时优先修最上游问题：

1. 任务模式、数量或参考图角色解析错误。
2. 人物身份漂移。
3. 年龄、骨架、身体结构漂移。
4. 摄影事件失效。
5. 动作和环境物理错误。
6. 构图、光影或场景保真错误。
7. 美颜、皮肤和局部质感问题。
8. API 参数错误。

GPT Image 2 返回 `image_generation_user_error` 时，必须先修改 Prompt、尺寸或输入图，不能原样盲目重试。

## 来源与许可

本 Skill 的增强层由 aoeking21 维护，采用 MIT License。摄影提示词基础方法派生自 `nuyoah-ai-works/nuyoah-xiezhen-prompt`，上游版权和许可证见 `THIRD_PARTY_LICENSE` 与 `NOTICE.md`。

外部摄影 Skill 在进入本仓库前必须先确认许可证和复用边界。许可不明确时，可以通过外部依赖或通用摄影知识接口使用其思想，不直接复制其源码、文本和资产。
