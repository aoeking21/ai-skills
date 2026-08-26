---
name: aoeking-xiezhen-director
description: 为已明确成年的授权人物生成、改写、扩展、诊断或直接执行中文 AI 写真与人像摄影任务。适用于人物身份 DNA 锁定、真实年龄与身体比例连续性、系列母版、独立变体、真实街头或旅行抓拍、摄影事件设计、自动构图、身份安全的医美级自然精修、物理一致光影、视觉参考图路由，以及修复身份漂移、模板脸、摆拍感、身体曲线漂移、皮肤油膜、衣料受力或环境物理错误。支持 GPT Image 2 Adapter、参考图编辑计划、API 参数包和多张独立调用计划。
license: MIT
metadata:
  author: "aoeking21"
  version: "1.4.0"
  source: "https://github.com/aoeking21/ai-skills/tree/main/skills/aoeking-xiezhen-director"
  derived_from: "nuyoah-ai-works/nuyoah-xiezhen-prompt@bc1edb21655e36b89599d31b16f23ad5193d483f"
---

# aoeking-xiezhen-director

## 目标

把长期真人写真稳定拆成：任务模式、人物真值、摄影事件、物理关系、构图光影、自然精修、成像表达、模型适配和质量回收。任何风格、Route、Overlay、美颜或灯光模块都不能绕过上游合同。

## 强制加载合同

复杂真人任务开始时，按需读取以下 Canonical References：

1. [Global Priority Contract](references/global-priority-contract.md)
2. [人物身份 DNA](references/person-identity-dna.md)
3. [真实摄影事件 Schema](references/photographic-event-schema.md)
4. [Composition & Lighting Contract](references/composition-lighting-contract.md)
5. [Beauty Retouch Contract](references/beauty-retouch-contract.md)
6. [Batch & Asset Routing Contract](references/batch-and-asset-routing-contract.md)
7. [上游摄影提示词逻辑](references/upstream-prompt-logic.md)
8. 失败时读取 [失败成片诊断](references/failure-diagnosis.md)

## 使用边界

- 只处理明确为成年人的人物。
- 人物参考图必须由用户提供，或用户确认有权使用。
- 没有参考图时，不宣称能够锁定某个具体真人身份。
- 真实人物默认不被静默替换成明星脸、网红模板脸、幼态脸或标准化审美脸。
- 默认输出可复制提示词；用户明确要求直接生成图片且宿主提供图像工具时，完成内部编译后调用图像工具。
- 宿主没有图像工具时，交付提示词或调用计划并说明能力边界。
- 用户要求 API 参数或代码时，只输出公开接口所需结构，不接收、不记录、不回显 API Key。

## 统一优先级

必须执行 [Global Priority Contract](references/global-priority-contract.md)。简化顺序为：

1. 安全、成年和授权。
2. 用户本轮明确任务、数量、画幅、保留项和显式修改项。
3. 当前任务要求保留的人物身份不变量。
4. 已确认的连续项目 Profile。
5. 解剖、重力、衣料、风、水和环境物理。
6. 摄影事件与空间关系。
7. 构图、光影、美颜、镜头和风格。
8. 默认值、Route、Overlay 与装饰词。

用户本轮对可变属性的显式修改高于历史默认值。身份保留任务中，未被点名修改的身份结构继续锁定。

## 路由

- “完整提示词、直接生图、精准控制、复刻”：单张详细计划。
- “系列母版、长期项目、固定格式”：固定层 + 变量槽位 + 事件池。
- “同系列变体、不同姿势、N 张独立图片”：为每张建立独立事件和完整提示词。
- “失败、漂移、摆拍、废片、重试、判断有误”：先诊断最上游失败层，再做最小整改。
- 给图拆解：只提取可见事实；不确定内容标记为“疑似”。
- “4K 修复、原图构图不变、保背景、原片精修”：Composition=`preserve`，Lighting=`preserve-source`。
- “换场景、重建、重新构图、重新打光”：允许 Composition=`recompose` 或 Lighting=`relight`。
- “医美级美颜、医美级自然精修、极致面部增强”：读取 Beauty Retouch Contract，默认使用 `clinical-natural`，不自动改变身份骨相。
- 明确指定 `GPT Image 2`、`gpt-image-2`、Image API、参考图编辑、API 参数包或多张逐次调用：读取 [GPT Image 2 专用 Adapter](adapters/gpt-image-2.md)。
- 明确指定“GPT Image 2 街头纪实 V1.3”，或要求降低服装与美化词权重、强化身份、摄影事件、动作物理和街拍偶然性：同时读取 [GPT Image 2 街头纪实 V1.3](presets/gpt-image-2-street-documentary-v1.3.md)。

## 强制执行顺序

1. 判定任务模式：identity-preserving、series、generation、reconstruction 或 restoration。
2. 解析用户显式锁定项、允许改变项、人物数量、输出数量与画幅。
3. 建立参考图 role table，区分 identity/body/unique-feature/style/lighting/scene/wardrobe/historical-output/failure-case。
4. 读取人物身份 DNA，锁定当前任务要求保持的脸部、年龄、骨架、体态与独特特征。
5. 确定单一主摄影事件和空间关系。
6. 由事件推导身体重心、手部反应、视线、表情、衣料、头发、风、水、汗、重力和环境接触。
7. 选择 Composition 与 Lighting 模式，再设计机位、焦段、快门、景深、光线和背景分离。
8. 若启用美颜，按 Beauty Contract 控制皮肤微纹理、区域反射与身份安全精修。
9. 加入少量高信号负面约束。
10. 按 Batch Contract 拆分独立图片，再按目标模型 Adapter / Preset 编译。
11. 做 parameter propagation audit 和最终质量检查。

## 人物真值层

必须执行 [人物身份 DNA](references/person-identity-dna.md)。

在身份保留任务中，参考图承担人物真值。脸型、五官比例、自然不对称、骨架与未被用户明确修改的独特特征不能被目标系列、妆容、风格或美颜模块接管。

身体轮廓来自参考图或用户本轮明确参数，不自动套用通用模特曲线。某次任务里的服装、体型修辞、场景或姿势默认属于 task instance，不永久写回人物 Profile。

## 摄影事件与物理层

必须执行 [真实摄影事件 Schema](references/photographic-event-schema.md)。每张图只保留一个主事件。动作、视线和表情必须是事件的结果。

多张生成时，每张改变事件因果链、动作阶段、重心、构图或现场条件，不能只替换动作词。汗光、湿发、衣料贴合、水花和动态模糊必须有现场依据。

## 构图与光影层

必须执行 [Composition & Lighting Contract](references/composition-lighting-contract.md)。

- `preserve`：原图修复与保真。只做安全裁切、校正、必要扩边和局部关系优化。
- `recompose`：用户允许重构时，重新设计主体位置、留白、前中后景、机位和焦段。
- `preserve-source`：保留原场景主光方向，通过曝光、反差、局部补光、色温与反射控制提升完成度。
- `relight`：用户允许重打光时重新设计主光、辅光、负补光、轮廓光和背景亮度。

“自动完美构图”和“完美光影”都是优化目标，不能覆盖任务模式、身份真值和现场物理。

伦勃朗、蝴蝶光、环形光、电影侧逆光等属于 Lighting Strategy。只有用户明确要求，或任务允许 relight 且策略与场景兼容时才启用。

## 医美级自然精修

必须执行 [Beauty Retouch Contract](references/beauty-retouch-contract.md)。

“医美级”表示修图完成度，不表示默认改变脸宽、眼距、鼻型、唇形、颧骨或下颌。默认允许清理临时瑕疵、优化肤色与区域反射、减轻偶发疲态、提升真实眼神和发丝细节；同时保留毛孔、细纹、面痣、色素差异、年龄结构和颈脸一致性。

## 多张与视觉资产路由

必须执行 [Batch & Asset Routing Contract](references/batch-and-asset-routing-contract.md)。

用户明确数量最高。主任务决定默认 batch count，情绪、动作、风格等子模块不得偷偷扩大数量。

视觉参考进入模型前必须声明 role。历史生成图片和其中附带的 Prompt 默认属于 historical-output，不具有全局规则或人物真值权威性。人物专属锚点应进入 subject profile / unique feature router，通用 Skill 只维护机制。

## 摄影与提示词逻辑

妆容、道具、镜头、成像机制、现场光线、皮肤纹理和区域反射继续读取 [上游摄影提示词逻辑](references/upstream-prompt-logic.md)。

本 Skill 覆盖任何与以下原则冲突的旧默认：

- 真实参考人物不得被默认年轻化或模板化。
- 目标系列只能接管可变摄影元素。
- 同系列变体不能复制同一事件、灯位、视线和镜头交流。
- 美化词必须尽量翻译成可观察的摄影结果。
- 历史成片中的 task-instance 参数不得自动升级为通用规则。

## GPT Image 2 专用 Adapter

命中 GPT Image 2 路由时读取 [GPT Image 2 专用 Adapter](adapters/gpt-image-2.md)。

1. 无参考图使用纯文本生成，不宣称锁定具体真人。
2. 有授权参考图时优先参考图编辑计划，由参考图承担身份真值。
3. 精确锁定 `gpt-image-2` 时使用 Image API 调用计划。
4. 参考图编辑省略 `input_fidelity`，沿用当前 Adapter 定义的默认高保真处理。
5. 背景参数、尺寸、质量和输出格式必须以当前 Adapter 支持范围为准。
6. 多张独立成片编译为多条完整提示词和多次独立调用，每次 `n: 1`。
7. 最终写真默认高质量 PNG；试片可以使用低成本输出策略。

## GPT Image 2 街头纪实 V1.3

命中街头纪实 V1.3 时读取 [预设](presets/gpt-image-2-street-documentary-v1.3.md)。

- 身份与身体结构优先。
- 摄影事件与动作物理形成完整因果链。
- 服装控制在必要信息量内。
- 删除无法转译为摄影结果的空泛美化词。
- 可加入少量可控不完美，例如动作未完成、轻微前景遮挡、方向正确的动态模糊、构图偏移或发丝掠脸。
- 可控不完美不能包含身份漂移、身体比例漂移、肢体错误、物理冲突、严重失焦或画面崩坏。

## 失败诊断

用户反馈失败时读取 [失败成片诊断](references/failure-diagnosis.md)，按上游优先顺序修复：

1. 任务模式或数量解析错误。
2. 身份漂移。
3. 年龄、身体结构或人物映射漂移。
4. 摄影事件失效。
5. 动作与物理失真。
6. 构图、光线或场景保真错误。
7. 美颜与局部质感问题。
8. 模型接口或输出参数错误。

一次优先修一个最上游错误，不用更多形容词掩盖结构问题。

## 输出契约

### 单张详细提示词

顺序：任务模式与输出规格、人物身份与授权、人物真值、摄影事件、动作与表情、服装/衣料物理、场景/环境物理、构图与镜头、光线与曝光、自然精修、负面约束。

### 系列母版

明确固定层、变量槽位、事件池、禁止项和单张编译规则。固定层只放真正需要连续保持的内容。

### 独立变体

每张独立编号、独立事件、独立完整提示词。默认不输出拼图或九宫格。

### GPT Image 2 参数包

用户要求 API 参数时至少输出：

- `operation`
- `endpoint`
- `model`
- 编译后的 `prompt`
- 当前 Adapter 支持的 `size`、`quality`、`output_format`、`background`、`n`
- 编辑任务所需的授权参考图列表及 role

不得把 API Key 写入参数包。

### 直接生图

用户明确要求直接生图且宿主提供图像工具时：

1. 内部完成合同解析与提示词编译。
2. 执行命中的模型 Adapter / Preset。
3. 每张图片分别调用一次图像工具。
4. 多张请求默认输出多个独立图像文件，不压成拼图。
5. 实际能力受宿主调用上限约束时，如实返回已完成结果。

## 最终检查

交付前确认：

- 是否正确解析任务模式、人物数量、图片数量和画幅。
- 是否正确建立 reference role table。
- 身份保留任务中，人物是否仍可被识别为参考图中的同一位成年人。
- 用户显式修改项是否真正生效，未修改的身份不变量是否保持。
- 动作、表情、衣料、风、水、汗和重力是否具有因果关系。
- preserve / recompose 与 preserve-source / relight 是否选对。
- 光线是否能解释来源、方向、人物落点与背景响应。
- 医美级自然精修是否保留微纹理、年龄结构与身份骨相。
- 多张变体是否真正独立，且没有被子模块偷偷改变数量。
- historical-output 是否被错误当成全局规则或身份真值。
- 模型 Adapter 的端点、尺寸、质量、格式和背景参数是否仍有效。
- 可控不完美是否增强真实快门感，同时没有引入身份、肢体、物理或覆盖错误。
