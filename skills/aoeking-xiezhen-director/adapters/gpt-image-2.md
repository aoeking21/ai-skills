# GPT Image 2 专用 Adapter

## 目标

把 `aoeking-xiezhen-director` 生成的人物写真意图编译成适合 `gpt-image-2` 的提示词、调用计划或 API 参数包。人物真值、摄影事件和真实物理仍由主 Skill 决定，本 Adapter 只负责模型路由、提示词压缩、输出尺寸和接口参数。

## 适用条件

出现以下任一意图时读取本 Adapter：

- 用户明确指定 `GPT Image 2`、`gpt-image-2` 或 GPT Image 2 API。
- 用户要求把写真提示词改成 GPT Image 2 专用格式。
- 用户提供人物参考图并要求生成、编辑或保持人物身份。
- 用户要求同时交付提示词和 API 调用参数。
- 用户要求通过 OpenAI Image API 连续生成多张独立成片。

## 已验证模型契约

- 默认模型别名：`gpt-image-2`。
- 可锁定快照：`gpt-image-2-2026-04-21`。
- 单次生成或编辑优先使用 Image API：
  - 新图：`POST /v1/images/generations`。
  - 参考图编辑：`POST /v1/images/edits`。
- Responses API 适合多轮对话式编辑，但图像工具自行选择 GPT Image 模型。任务必须精确锁定 `gpt-image-2` 时，使用 Image API。
- `gpt-image-2` 对所有输入图自动执行高保真处理。编辑请求必须省略 `input_fidelity`，不得写入 `low` 或 `high`。
- `background` 只使用 `auto` 或 `opaque`。当前模型不支持 `transparent`。
- 输出格式支持 `png`、`jpeg`、`webp`。JPEG 与 WebP 可使用 `output_compression`。

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

参考图承担人物身份真值。提示词明确哪些内容必须保持，哪些摄影变量允许改变。

### 3. 多轮连续修改

用户需要围绕同一结果持续修改时，可以使用 Responses API 图像工具。输出中要说明：Responses API 由工具选择图像模型，无法通过图像工具参数精确固定 `gpt-image-2`。

### 4. 多张独立成片

用户要求五张独立图片时：

1. 先编译五条独立完整提示词。
2. 每条提示词使用一次独立 API 调用。
3. 每次设置 `n: 1`。
4. 不把五条提示词合并到一个请求。
5. 不生成拼图、五宫格或同一画布中的重复人物。

## 提示词编译顺序

最终提交给 GPT Image 2 的提示词按以下顺序组织：

1. **任务与画幅**：照片类型、横竖幅、完整全身或景别。
2. **人物身份真值**：同一位成年人、脸型、年龄、肤色、骨架和稳定识别点。
3. **保持项与允许变化项**：参考图中必须保留的内容，以及服装、场景、动作等可变量。
4. **单一摄影事件**：这一秒发生的刺激与本能反应。
5. **身体与物理结果**：重心、支撑脚、手部任务、衣料、头发、风、水、汗和地面承重。
6. **表情与视线**：由事件产生，避免持续镜头交流。
7. **构图与镜头**：机位、焦段、透视、快门、景深和允许的动态模糊。
8. **光线与肤感**：来源、方向、落点、曝光、微纹理和区域反射。
9. **输出规格**：尺寸、质量、成像媒介和单张画布。
10. **高信号禁止项**：只保留会直接破坏身份、事件或物理的约束。

## GPT Image 2 提示词规则

- 使用完整、自然、可观察的中文摄影描述。
- 优先写正向结果，例如“视线落向风吹来的方向”，少写抽象否定词。
- 相互关联的约束放在同一段中，避免把人物、动作和风向拆成互不相干的关键词。
- 身份保持使用具体结构描述，避免只写“锁脸”“高度一致”。
- 参考图编辑时，明确“只改变”与“保持不变”的边界。
- 摄影事件只保留一个主因果链。
- 五张独立需求必须生成五条不同事件链。
- 不在提示词中写模型无法执行的流程承诺，例如“连续自动生成五次”。调用层负责实际执行次数。

## 尺寸映射

优先使用以下满足 GPT Image 2 尺寸约束的分辨率：

| 画幅 | 推荐尺寸 | 用途 |
|---|---:|---|
| 1:1 | `1024x1024` | 方形头像、封面 |
| 2:3 | `1024x1536` | 标准竖幅人像 |
| 3:4 | `1152x1536` | 写真与半身、全身人像 |
| 4:5 | `1280x1600` | 社交媒体竖幅 |
| 9:16 | `1152x2048` | 手机全屏、动态抓拍 |
| 16:9 | `2048x1152` | 横幅环境人像 |

自定义尺寸必须同时满足：

- 两条边都是 16 的倍数。
- 最长边不超过 3840 像素。
- 长短边比例不超过 3:1。
- 总像素不少于 655,360 且不超过 8,294,400。
- 超过 2K 级别时标记为实验性输出，优先先用标准尺寸验证提示词。

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

人物身份、皮肤纹理和细小衣料细节为验收重点时，最终输出优先使用 `high + png`。

## 生成请求参数包

当用户要求 API 参数时，输出以下结构：

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

参考图编辑时：

```json
{
  "adapter": "gpt-image-2",
  "operation": "edit",
  "endpoint": "/v1/images/edits",
  "model": "gpt-image-2",
  "images": ["<授权人物参考图>"],
  "prompt": "<保持人物真值并改变摄影条件的完整提示词>",
  "size": "1152x2048",
  "quality": "high",
  "output_format": "png",
  "background": "auto",
  "n": 1
}
```

编辑参数包中禁止出现 `input_fidelity`。

## 输出模式

根据用户需求交付一种或多种结果：

- `prompt_only`：只输出可复制的 GPT Image 2 提示词。
- `prompt_and_parameters`：输出提示词与 API 参数包。
- `independent_batch_plan`：输出多条独立提示词和逐次调用计划。
- `code_sample`：用户明确要求代码时，再输出 Python、JavaScript、curl 或 OpenAI CLI 示例。

## 失败整改映射

| 失败 | Adapter 处理 |
|---|---|
| 人物身份漂移 | 改用 `images.edit` 并提供授权参考图；减少妆容、发型和情绪变量；加强具体身份锚点 |
| 年龄或体态漂移 | 在人物真值段写明年龄、胸廓、肩颈、腰臀差和四肢比例 |
| 摆拍感 | 重写单一摄影事件、手部现实任务、支撑脚与视线目标 |
| 风、水、衣料冲突 | 统一方向、接触点、重力和动作阶段 |
| 全脸油膜 | 降低正面强闪和过曝，限定 T 区窄高光与双颊漫反射 |
| 多张高度重复 | 每张使用独立事件、独立构图和独立 API 调用 |
| 透明背景报错 | 将 `background` 改为 `auto` 或 `opaque` |
| 编辑参数报错 | 删除 `input_fidelity`，保留 `gpt-image-2` 默认高保真输入处理 |

## 交付前检查

- 使用的模型名称是否为 `gpt-image-2` 或用户明确要求的快照。
- 生成和编辑端点是否选择正确。
- 参考图编辑是否省略 `input_fidelity`。
- 背景是否避免 `transparent`。
- 尺寸是否满足 16 像素倍数、像素总量和比例限制。
- 多张独立成片是否拆成多条提示词与多次调用。
- 提示词是否先锁定人物真值，再描述摄影事件和成像表达。
- API 参数和提示词是否没有互相冲突。

## 官方依据

本 Adapter 于 2026-08-01 按 OpenAI 官方资料校准：

- GPT Image 2 模型页：`https://developers.openai.com/api/docs/models/gpt-image-2`
- Image generation 指南：`https://developers.openai.com/api/docs/guides/image-generation`
- GPT Image prompting guide：`https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide`
