# GPT Image 2 专用 Adapter

校准日期：2026-08-27

## 目标

把 `aoeking-xiezhen-director` 的写真意图编译成适合 `gpt-image-2` 的提示词、调用计划或 API 参数包。人物真值、摄影事件、构图/光影模式、自然精修和真实物理由主 Skill 决定，本 Adapter 只负责模型路由、输出尺寸、格式和接口参数。

## 适用条件

出现以下任一意图时读取本 Adapter：

- 用户明确指定 `GPT Image 2`、`gpt-image-2` 或 GPT Image 2 API。
- 用户要求把写真提示词改成 GPT Image 2 专用格式。
- 用户提供授权人物参考图并要求生成、编辑或保持人物身份。
- 用户要求同时交付提示词和 API 调用参数。
- 用户要求通过 OpenAI Image API 连续生成多张独立成片。
- 用户要求 4K 修复、4K 竖图或自定义比例输出。

## 已验证模型契约

- 默认模型别名：`gpt-image-2`。
- 可锁定快照：`gpt-image-2-2026-04-21`。
- 单次生成或编辑优先使用 Image API：
  - 新图：`POST /v1/images/generations`。
  - 参考图编辑：`POST /v1/images/edits`。
- Responses API 更适合多轮、对话式高保真编辑，但图像生成工具自行选择 GPT Image 模型；需要精确固定 `gpt-image-2` 时使用 Image API。
- `gpt-image-2` 对输入图自动执行高保真处理。编辑请求必须省略 `input_fidelity`，API 不允许为该模型改成 `low` 或 `high`。
- `background` 使用 `auto` 或 `opaque`。当前 `gpt-image-2` 不支持 `transparent`。
- 输出格式支持 `png`、`jpeg`、`webp`。JPEG 与 WebP 可使用 `output_compression`。
- `size`、`quality`、`background` 均支持 `auto`。
- `quality` 支持 `low`、`medium`、`high`、`auto`。

## 路由决策

### 1. 纯文本生成

没有参考图时：

```text
endpoint: images.generate
model: gpt-image-2
```

人物身份只能来自文字描述，不宣称锁定具体真人。

### 2. 授权参考图生成或编辑

存在授权人物参考图时：

```text
endpoint: images.edit
model: gpt-image-2
image: one or more authorized reference images
```

参考图先经过主 Skill 的 role table。`identity_anchor` 承担人物身份真值；style、lighting、scene、wardrobe 等参考只能控制对应可变层。

### 3. 多轮连续修改

用户需要围绕同一结果持续修改时，可以使用 Responses API 图像工具。若任务要求精确固定 `gpt-image-2`，继续使用 Image API，并由上层会话保存参考图和上轮结果。

### 4. 多张独立成片

多张任务执行 [Batch & Asset Routing Contract](../references/batch-and-asset-routing-contract.md)：

1. 每张编译独立完整提示词与 Event Card。
2. 身份保留任务每张继续使用原始授权身份参考图。
3. 默认每次 `n: 1`，便于单张验收、失败定位和定向重试。
4. 不把不同事件压成拼图或同一画布中的重复人物，除非用户明确要求这种排版。

## 提示词编译顺序

1. 任务模式、数量、画幅与输出目标。
2. 人物身份真值和参考图角色。
3. 保持项、允许变化项与本轮 override。
4. 单一摄影事件。
5. 身体重心、支撑、手部任务、衣料、头发、风、水、汗、重力和环境接触。
6. 表情与视线。
7. preserve/recompose 构图模式、机位、焦段、快门、景深。
8. preserve-source/relight 光影模式、主光来源、方向、落点、曝光与背景响应。
9. Beauty Contract 要求的真实皮肤微纹理与区域反射。
10. 输出规格与少量高信号禁止项。

## GPT Image 2 提示词规则

- 使用完整、自然、可观察的摄影描述。
- 优先写正向视觉结果，降低空泛审美词和重复否定词。
- 相互关联的身份、动作、风向、衣料和灯光约束放在同一因果链中。
- 身份保持使用具体结构和参考图角色，不只写“锁脸”。
- 参考图编辑明确“保持”与“允许改变”的边界。
- 一张图只保留一个主摄影事件。
- 调用层负责次数、参数、失败分类和重试，提示词不承诺模型无法自行执行的多次操作。

## 尺寸映射

GPT Image 2 支持大量自定义分辨率。所有尺寸必须满足：

- 两条边都是 16 的倍数。
- 最长边不超过 `3840px`。
- 长边与短边之比不超过 `3:1`。
- 总像素不少于 `655,360`，不超过 `8,294,400`。

推荐尺寸：

| 画幅 | 推荐尺寸 | 用途 |
|---|---:|---|
| 1:1 | `1024x1024` | 头像、封面、快速试片 |
| 2:3 | `1024x1536` | 标准竖幅人像 |
| 3:4 | `1152x1536` | 写真、半身、全身 |
| 4:5 | `1280x1600` | 社交媒体竖幅 |
| 9:16 | `1152x2048` | 手机全屏、动态抓拍 |
| 16:9 | `2048x1152` | 横幅环境人像 |
| 4K 9:16 | `2160x3840` | 最终高分辨率竖幅 |
| 4K 16:9 | `3840x2160` | 最终高分辨率横幅 |

`2160x3840` 和 `3840x2160` 已属于官方列出的 GPT Image 2 常用 4K 尺寸，不再标记为“实验性”。

如果用户要求“长边 4096”，当前模型尺寸上限为 3840，调用层必须明确降级到最大合规尺寸，或先生成 3840 长边版本，再由独立的超分辨率后处理模块完成 4096 交付。不得把 4096 直接伪装成 GPT Image 2 原生合法尺寸。

## 质量与格式默认值

### 最终写真

```json
{
  "quality": "high",
  "output_format": "png",
  "background": "auto",
  "n": 1
}
```

### 快速试片

```json
{
  "quality": "low",
  "output_format": "jpeg",
  "output_compression": 85,
  "background": "auto",
  "n": 1
}
```

### 平衡迭代

```json
{
  "quality": "medium",
  "output_format": "png",
  "background": "auto",
  "n": 1
}
```

人物身份、面部纹理、发丝和衣料细节是验收重点时，最终输出优先 `high + png`。如果微信回图的传输时延或文件大小成为瓶颈，产品层可以保存 PNG 母版，同时生成 JPEG/WebP 派生交付文件，不修改母版。

## 4K 修复策略

当用户要求 4K 修复：

1. 先判定主任务是 `restoration`，默认 Composition=`preserve`、Lighting=`preserve-source`。
2. 身份参考图进入 `images.edit`。
3. 优先使用与原图方向和比例接近的合规高分辨率尺寸。
4. 9:16 可使用 `2160x3840`；16:9 可使用 `3840x2160`。
5. 其他比例计算最近的 16 像素倍数，且总像素不超过官方限制。
6. 用户强制要求长边 4096 时，GPT Image 2 先完成最大 3840 长边生成，再进入独立超分步骤。
7. 4K 修复不得因为高分辨率目标擅自重构脸型、背景或主光方向。

## 生成请求参数包

示例：

```json
{
  "adapter": "gpt-image-2",
  "operation": "generate",
  "endpoint": "/v1/images/generations",
  "model": "gpt-image-2",
  "prompt": "<编译后的完整提示词>",
  "size": "1152x2048",
  "quality": "high",
  "output_format": "png",
  "background": "auto",
  "n": 1
}
```

参考图编辑：

```json
{
  "adapter": "gpt-image-2",
  "operation": "edit",
  "endpoint": "/v1/images/edits",
  "model": "gpt-image-2",
  "images": ["<授权人物参考图>"],
  "prompt": "<保持人物真值并改变允许摄影变量的完整提示词>",
  "size": "1152x2048",
  "quality": "high",
  "output_format": "png",
  "background": "auto",
  "n": 1
}
```

编辑参数包禁止出现 `input_fidelity`。

## 错误分类与重试

自动化系统不得对所有失败机械重试。

- 网络超时、服务暂时错误等可恢复故障：允许按产品层重试策略重试。
- `image_generation_user_error`：先修改 Prompt、尺寸或输入图，再提交；不能原样自动重试。
- moderation / safety block：按返回的稳定错误 code 和 moderation details 调整任务输入，不进行相同请求的盲目循环。
- 参数错误：先做 Adapter 预检，修正尺寸、背景、格式和不支持字段。
- 视觉质量失败：进入主 Skill 的 Failure Diagnosis，只重写最上游失败层，再重新生成。

## 失败整改映射

| 失败 | Adapter 处理 |
|---|---|
| 人物身份漂移 | 使用 `images.edit` + identity anchor；减少互相冲突的妆容/风格变量 |
| 年龄或体态漂移 | 回到人物真值与 Global Priority Contract 修复 |
| 摆拍感 | 重写单一摄影事件、现实手部任务、重心和视线 |
| 风、水、衣料冲突 | 统一方向、接触点、重力与动作阶段 |
| 全脸油膜 | 执行 Beauty Contract 的区域反射规则 |
| 多张高度重复 | 每张使用独立 Event Card 和独立调用 |
| 透明背景报错 | `background` 改为 `auto` 或 `opaque` |
| 编辑参数报错 | 删除 `input_fidelity` |
| 4096 尺寸报错 | 改为 3840 最大边合规尺寸，再独立超分 |
| user error | 修改请求后再提交，禁止原样盲重试 |

## 交付前检查

- 模型名称是 `gpt-image-2` 或用户明确要求的快照。
- generation/edit endpoint 选择正确。
- reference role table 已建立。
- 编辑任务省略 `input_fidelity`。
- `background` 未使用 `transparent`。
- 尺寸满足 16 倍数、最大边、比例和总像素限制。
- 4096 长边没有被错误当成原生合法尺寸。
- 多张任务遵守 Batch Contract。
- preserve/recompose 与 preserve-source/relight 没有被 Adapter 改写。
- API 参数和最终 Prompt 没有互相冲突。

## 官方依据

本 Adapter 于 2026-08-27 依据 OpenAI 官方资料重新校准：

- GPT Image 2 模型页：`https://developers.openai.com/api/docs/models/gpt-image-2`
- Image generation 指南：`https://developers.openai.com/api/docs/guides/image-generation`
- GPT Image prompting guide：`https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide`
