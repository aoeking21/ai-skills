# Mandatory Invocation and Image Generation Contract V2

本合同用于 portrait-master-director 的强制调用、提示编译与图像生成门控。目标是让“portrait-master-director”与“人像摄影”成为可审计的强激活词，避免识别到 Skill 后直接绕过读取流程进入图像生成。

## 1. 强激活词

以下任一条件出现即设置 `MANDATORY_SKILL_TRIGGER=true`：

- 用户明确写出 `portrait-master-director`。
- 用户明确写出“人像摄影”，且上下文是创建、编辑、重绘、修复或生成成年人物图像。
- 用户明确要求“调用 portrait-master-director / 调用 Skill 后出图”。

强激活后，本轮禁止把该词仅作为风格描述处理。

## 2. 生成前硬门

进入任何图像生成器前必须完成并记录：

1. `skill_loaded=true`：已实际读取当前仓库中的 `SKILL.md`。
2. `required_references_loaded=true`：已读取本任务所需合同。身份保持任务至少读取 `reference-asset-router.md` 与 `quality-gate.md`；本合同必须读取。
3. `current_upload_bound=true`：身份保持任务已把本轮用户上传的真实原图绑定为 `current_upload` / `identity_primary`。
4. `profile_activation_explicit`：没有显式 Profile 时必须为 `false`，禁止静默加载历史人物资产。
5. `task_contract_compiled=true`：用户本轮要求已经编译成任务合同。
6. `safety_reviewed=true`。
7. `prompt_compiled=true`：最终图像指令已从任务合同编译完成。

任一必需项缺失：`PRE_GENERATION_GATE=FAIL`，禁止调用图像生成器，返回可诊断失败原因。不得静默降级为普通原生出图。

## 3. Task Contract

身份保持的人像任务至少解析以下字段：

- `identity_source`
- `subject_count`
- `task_mode`
- `scene`
- `wardrobe`
- `body_constraints`
- `expression`
- `pose_action`
- `camera_composition`
- `lighting_weather`
- `photographic_style`
- `protected_domains`
- `allowed_changes`
- `negative_constraints`

用户未指定的视觉字段允许由 Portrait Director 自主补全，但不得覆盖用户明确要求或身份不变量。

## 4. Portrait Director

### 身份

本轮真实上传图是身份真值。优先保持可识别的脸型、额头与发际线、眉眼结构、鼻唇结构、下颌、真实年龄观感、肤色、发型基线、眼镜等显著特征。禁止模板脸、网红脸、陌生人化、无请求的年轻化、跨人物混合。

### 身体

用户明确指定体态、曲线、胸廓或整体比例时，将其作为本轮生成目标；仍保持解剖可信、承重可信、衣料受力可信。不得自行夸张性征。

### 动作与神态

“抓拍、漫步、回眸、未完成的笑”等要求优先转译为连续动作中的自然瞬间。避免僵硬站桩、过度对称、广告式固定微笑和无理由直视镜头。用户明确要求看镜头时遵从。

### 摄影物理

保持真实镜头透视、景深、运动模糊、雨雾、皮肤高光、湿发、衣料湿润与环境反射之间的物理一致性。真实摄影任务避免塑料皮肤、过度磨皮、HDR 轮廓和 AI 式锐化。

### 场景与光影

环境承担叙事功能。天气、地面反射、背景层次、色温和人物受光应属于同一物理场。用户要求具体城市时，以可泛化的真实街景语汇表现；没有要求地标时不强行加入文字或著名地标。

## 5. Prompt Compiler

最终图像指令按以下优先级编译：

1. 安全与授权
2. 用户本轮明确要求
3. current_upload 身份约束
4. protected_domains
5. 人体与摄影物理
6. 动作、构图、光影
7. 默认审美补全

编译时避免把内部治理术语、JSON 状态或 Quality Gate 字段直接变成画面文字。品牌服装要求应描述为用户请求的视觉服装特征；图像模型无法可靠生成精确商标文字时，不把文字准确性置于人物身份之上。

## 6. 生成后视觉质量门

除治理 Quality Gate 外，人像输出还应检查：

- `IDENTITY_CONSISTENCY`
- `FACE_GEOMETRY`
- `AGE_PRESERVATION`
- `DISTINCTIVE_FEATURES`
- `SUBJECT_COUNT`
- `BODY_CONSTRAINT_COMPLIANCE`
- `WARDROBE_COMPLIANCE`
- `SCENE_COMPLIANCE`
- `POSE_ACTION_COMPLIANCE`
- `PHOTOGRAPHIC_REALISM`
- `ANATOMY_INTEGRITY`

能可靠检查的项目出现明显失败时进入有界返修，默认最多 2 轮。无法从当前工具链可靠测量的项目必须标记 `not_measurable`，不得伪造数值相似度或宣称像素级身份验证。

## 7. 可审计状态

用户询问“调用 Skill 了吗”时，只能按真实执行轨迹回答：

- `SKILL_NOT_LOADED`：未实际读取 SKILL.md。
- `SKILL_LOADED_GATE_FAILED`：Skill 已读取，但生成前门失败。
- `SKILL_EXECUTED_GENERATION_ATTEMPTED`：读取、编译和生成前门完成，已尝试生成。
- `SKILL_EXECUTED_GENERATION_COMPLETED`：生成完成，并执行可用的输出检查。

禁止仅凭看见激活词就回答“已调用”。

## 8. 能力边界

本合同约束遵循该 Skill 的代理执行流程，但不能改变宿主产品本身的工具路由实现。若当前运行环境无法实际读取 Skill、无法访问必需引用、缺少上传图或图像生成器拒绝请求，应明确报告对应状态，不得声称已经完整执行。
