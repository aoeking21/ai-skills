# Batch & Asset Routing Contract V1.0

本合同统一单张/多张解析，并规定 `/咪咪的影集`、历史生成图和人物专属锚点如何进入写真工作流。

## 1. 输出数量解析

优先级：

1. 用户明确数字，例如“1 张、4 张、五张独立图片”。
2. 主任务模式的默认 batch count。
3. 子风格、情绪、动作库的默认值。

同一条指令中，子模块不得擅自扩大主任务的输出数量。

推荐默认：

- `大师出片 / 单张精品 / 修图重试 / 特征出片`：1 张。
- 单独 `情绪大片`：可使用系列默认数量；若宿主未定义，先按 1 张执行。
- `一键出片 / 多动作 / 系列变体`：按明确数量；没有明确数量时由宿主产品层决定，Skill 不硬编码五张。

当“摄影大师出片 + 情绪大片”组合时，主任务 `大师出片` 决定 1 张，`情绪大片` 只改变情绪和事件表达。

## 2. 多张独立成片

多张任务必须：

- 每张独立 Prompt / Event Card。
- 每次保持原始授权参考图为身份真值。
- 改变至少两项高价值变量：事件阶段、重心、支撑脚、视线、机位、前景、景别或现场条件。
- 默认不输出拼图、九宫格、分屏或动作说明板。

## 3. 视觉资产角色

任何图片进入模型前必须声明 role：

- `identity_anchor`：脸部和人物身份真值。
- `body_anchor`：真实体态、骨架、比例。
- `unique_feature_anchor`：纹身、眼镜、特殊饰品等独特特征。
- `style_reference`：色彩、构图、摄影语言。
- `lighting_reference`：主光、光比、阴影与背景明暗。
- `scene_reference`：空间、材质、地点结构。
- `wardrobe_reference`：服装版型、材料、配色。
- `historical_output`：历史生成结果，仅供评估。
- `failure_case`：失败诊断样本。

同一图片可以有多个 role，但 `historical_output` 默认没有身份真值权威性。

## 4. `/咪咪的影集` 的使用边界

该数据源属于视觉知识库。系统不能因为检索到相似图片，就自动把其中某次任务的体型、服装、场景、妆容或动作写入当前人物 Profile。

只有显式登记为 `identity_anchor / body_anchor / unique_feature_anchor` 的图片才能进入人物真值层。

人物专属规则，例如背部凤凰纹身，应进入 subject profile + unique feature router。通用 Skill 只维护路由机制，不硬编码某个具体人物的私有视觉特征。

## 5. 历史 Prompt 与成片

PNG/JPEG 中附带或可检索到的历史 Prompt 统一视为 `historical_output metadata`。

允许：

- 提取成功构图、光影或物理模式。
- 用作 Eval 或 Failure Diagnosis。
- 经人工确认后提升为 Preset / Reference。

禁止：

- 直接作为全局最高规则。
- 将单次人物体型、服装或场景覆盖新任务。
- 因关键词相似就覆盖本轮用户要求。

## 6. 规则资产与视觉资产分层

- GitHub：规则、路由、Adapter、Preset、Eval、版本和 CI。
- Library：原图、视觉锚点、案例、历史输出和大型数据集。

Prompt Compiler 只加载当前任务必需的最小规则集合与最少视觉锚点，避免把整库文本和整批图片一次性送入模型。
