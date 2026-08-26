# 摄影图像资产总盘点 V1.0

状态：Baseline Inventory  
分支：`repair/photography-assets-v1`  
目的：先冻结并识别现有资产，再进行去重、冲突消解、重构与修复。原始资料在本阶段不删除。

## 1. 盘点范围

本次盘点覆盖三类来源：

1. ChatGPT Library 项目 `/咪咪的影集`：真实人物照片、参考图、历史生成图、成功案例、失败案例、带提示词成片与压缩包。
2. GitHub `aoeking21/ai-skills`：摄影、人像、写真、身份锁定、构图、光影、模型适配、路由、测试与 Agent Skill 工程资料。
3. 外部参考 `okooo5km/rembrandt-portrait-lighting`：伦勃朗肖像光影方法。作为外部知识源评估，未确认授权边界前不直接复制其正文或资产进入本仓库。

## 2. 总体判断

现有资产并不缺能力，主要问题是长期迭代后出现了多个“权威入口”。同一概念在 Library 总库、历史激活表、生成图片内嵌提示词、GitHub Skill、上游快照、发行镜像中反复出现，导致规则重复、版本漂移、优先级不一致和调用歧义。

后续工程目标是建立单一事实源 Single Source of Truth，同时保留历史资料作为 archive、examples 或 evals，不再允许历史成片中的临时任务参数反向污染全局规则。

## 3. GitHub 资产地图

### 3.1 `skills/aoeking-xiezhen-director`

建议定位：**授权真人写真与连续人物项目的核心 Canonical Skill**。

已确认包含：

- `SKILL.md`
- `manifest.json`
- `agents/interface.yaml`
- `agents/openai.yaml`
- `adapters/gpt-image-2.md`
- `presets/gpt-image-2-street-documentary-v1.3.md`
- `evals/trigger_cases.json`
- `evals/quality_cases.json`
- `evals/gpt_image_2_cases.json`
- `evals/street_documentary_v1_3_cases.json`
- `references/person-identity-dna.md`
- `references/photographic-event-schema.md`
- `references/failure-diagnosis.md`
- `references/upstream-prompt-logic.md`

当前版本：`1.3.0`。

核心价值：人物真值、摄影事件、成像表达三层模型；授权真人身份锁定；GPT Image 2 Adapter；街头纪实预设；失败诊断；多张独立调用计划。

### 3.2 `image-generation/female-portrait-director`

建议定位：**女性人像风格导演与视觉路由 Canonical Library**。

已确认包含：

- 根 `SKILL.md`
- `skill/core/` 参数锁定、参考图锁定、冲突处理、安全边界、输出契约、导演门控
- `skill/routes/` 多类写真路线
- `skill/overlays/` 气质叠加层
- `skill/tools/` 优化、诊断、反推、参考图生成等工具
- `runtime/` 运行时与测试
- `assets/cases/` 成片案例
- `examples/` 示例
- `docs/` 版本、安全、风格等文档

发现：仓库内部同时存在 `image-generation/female-portrait-director/skills/female-portrait-director/` 的第二套近完整发行镜像。大量文件 SHA 相同，部分文件 SHA 不同，已经形成“重复 + 漂移”风险。

### 3.3 `image-generation/nuyoah-xiezhen-prompt`

建议定位：**上游来源快照 + 历史兼容层**。

包含：

- `upstream/`：上游原始快照、SOURCE、LICENSE、SKILL、manifest、references
- `aoeking-enhanced/`：早期增强版

发现：`aoeking-enhanced/SKILL.md` 的 `name` 仍为 `aoeking-xiezhen-director`，版本 `1.0.0`；而正式 `skills/aoeking-xiezhen-director/SKILL.md` 同名，版本 `1.3.0`。这是 P0 级 Skill 名称碰撞。

### 3.4 `scripts` 与 CI

现有：

- `scripts/validate_agent_skills.py`
- `scripts/validate_skill_integrity.py`
- `.github/workflows/validate-agent-skills.yml`
- `.github/workflows/validate-skill-integrity.yml`
- `.github/workflows/test-female-portrait-runtime.yml`

现有校验重点是 canonical `skills/*`、Markdown 链接、female-portrait Route 注册与依赖闭包。当前没有仓库级检测：

- 跨目录重复 Skill name
- canonical 与 distribution mirror 语义漂移
- manifest 与 Skill 版本漂移
- 旧兼容层误被当作新入口

## 4. Library 与“咪咪的影集”资产地图

### 4.1 `/咪咪的影集`

已确认包含大量 JPEG、PNG、历史生成结果与至少一个 ZIP 包。资产同时承担以下角色：

- 人物身份视觉锚点
- 面部参考
- 身体与体态参考
- 纹身等独特特征参考
- 构图参考
- 光影参考
- 场景参考
- 成功成片
- 历史实验结果
- 带提示词的生成结果

必须在后续建立 image-role metadata。未经分类的历史成片不能自动升级为人物真值或全局规则。

### 4.2 Library 正式规则资产

已确认存在：

- `AI图像生成提示词总库_V2.6_视觉命题关系场增强版.md`
- `001_V2.6_模块索引_视觉命题关系场增强版.csv`
- `003_V2.6_简明激活表_视觉命题关系场增强版.md`
- 多套 V2.3 / V2.4 / V2.5 / V2.5.1 历史主库、索引与激活表
- `正确出图顺序总控条款_摄影大师出片原图场景锁定版_正式并库终稿.md`
- 高写实摄影、人像摄影、写真、照片修复、表情、动作等历史数据库或索引引用

V2.6 已明确引入：视觉命题、场景契约、四层空间、成像因果、动作骨架、固定变量/自由变量、低噪音、批次实验、选片与错误回收闭环。

## 5. 已确认的重复与冲突

### P0-01：同名 Skill 碰撞

`image-generation/nuyoah-xiezhen-prompt/aoeking-enhanced/SKILL.md` 与 `skills/aoeking-xiezhen-director/SKILL.md` 使用同一个 Skill name。

风险：不同宿主、扫描路径或安装脚本可能加载不同版本。

处理：正式版本保留 `aoeking-xiezhen-director`；早期增强版改为 legacy bridge，禁止再作为同名入口。

### P0-02：female-portrait-director 双份实现

源码树与 `skills/female-portrait-director/` 发行镜像并存，且部分文件存在 SHA 漂移。

风险：修改一套后另一套未同步，测试通过但安装包运行旧规则。

处理：声明 canonical authoring source；发行镜像改为 generated/distribution mirror；新增 CI 语义一致性检测。

### P0-03：V2.6 与“V2.6.1”引用漂移

Library 可确认正式主库文件名为 V2.6；大量近期生成图片内嵌提示词调用“V2.6.1”。当前盘点没有确认独立正式 `AI图像生成提示词总库_V2.6.1...md` 主文件。

风险：出现幽灵版本，调用器无法知道 V2.6.1 对应哪份规则。

处理：在修复阶段建立明确版本别名或正式补丁说明。没有真实独立规则差异时，禁止伪造新主库内容。

### P1-01：人物身份优先级表达不统一

`aoeking-xiezhen-director` 将本轮用户要求置于最高输入优先级；`female-portrait-director` 冲突规则把参考图人物锁定列为 P0.5、用户参数列为 P1。

处理：建立统一 Global Priority Contract，区分“用户修改意图”和“身份不变量”。用户可明确改变服装、发型、背景、构图等可变项；需要同一真人时，身份结构不能被风格模块静默覆盖。

### P1-02：“医美级美颜”与“禁止医美化”语义冲突

历史“摄影大师出片”要求“医美级自然精修”；近期身份锁定提示词又经常写“禁止医美化”。

处理：统一术语为“医美级自然精修”，定义其为 retouch quality，不等同于 facial anatomy reshaping。默认允许临时瑕疵清理、肤色/反射/眼下状态优化、质感提升；默认禁止换脸、改骨相、模板五官、年龄坍缩、塑料磨皮。

### P1-03：“完美构图”与原图场景/构图锁定冲突

原图精修任务要求保留原人物位置、场景、空间关系；自动构图模块可能希望裁切、移动或重建。

处理：建立两种模式：

- `preserve`：原图精修，只允许安全裁切、轻微扩边和局部关系优化。
- `recompose`：用户允许重构时，自动优化构图、机位、留白与场景关系。

### P1-04：“完美光影”与原始光源方向锁定冲突

原图修复任务不能为了审美擅自改变太阳、窗光、路灯等主光方向。

处理：建立 Lighting Contract。保真模式下优化曝光、反差、局部补光、色温与阴影可读性；主光方向保持原现场逻辑。重构模式才允许重新设计灯位。

### P1-05：单张/五张默认数量在不同激活表中语义交叉

V2.6 简明激活表中，“大师出片”默认 1 张，“情绪大片”默认 5 张；旧版专项规则中，“摄影大师出片 + 情绪大片”仍要求 1 张。

处理：命令组合采用主任务决定 batch count。`大师出片` 命中时默认 1；单独 `情绪大片` 可默认 5；用户明确数量始终覆盖默认值。

### P1-06：历史成片内嵌 Prompt 污染规则层

Library 中大量 PNG/JPEG 含完整提示词，部分包含仅针对某次人物、某次体型、某件服装、某种场景的参数。

处理：统一归类为 `examples / evals / historical-output`，默认不得作为全局规则检索结果。只有被人工提升为 reference/preset 的片段才能进入规则层。

### P1-07：人物专属规则混入通用总库

例如“咪咪真实背部凤凰纹身图片强制调用”属于人物 Profile / Reference Router，不应成为所有人的通用摄影规则。

处理：迁移为 subject-specific profile。通用 Skill 只定义“独特身份特征如何路由参考图”的机制。

### P1-08：外部 Rembrandt Skill 的复用边界未固化

外部仓库已确认存在 `SKILL.md`、agents、assets、references，但根目录盘点未看到明确 LICENSE 文件。

处理：当前只吸收通用摄影知识与接口思想；在许可确认前不整库复制，不把外部 assets 当作本仓库资产。

## 6. 单一事实源设计

建议固定以下职责：

| 层 | Canonical Source | 职责 |
|---|---|---|
| 真人身份与连续性 | `skills/aoeking-xiezhen-director` | 人物真值、摄影事件、物理、失败诊断、模型适配 |
| 女性人像风格 | `image-generation/female-portrait-director` | Route、Overlay、风格导演、商业与写真视觉语言 |
| 上游来源 | `image-generation/nuyoah-xiezhen-prompt/upstream` | 来源追溯，不直接作为最新执行入口 |
| 历史兼容 | `.../aoeking-enhanced` | Legacy bridge，指向 canonical |
| Library 总纲 | V2.6 正式主库及其正式索引 | 视觉命题、场景契约、低噪音、关系场、模块目录 |
| 视觉参考 | `/咪咪的影集` | 原图、身份锚点、特征锚点、案例、实验结果 |
| 外部光影 | `rembrandt-portrait-lighting` | 外部 lighting reference / adapter candidate |

## 7. 新总 Skill 的目标边界

本轮修复完成后，再建立新的 Master Director。新 Skill 不复制所有数据库正文，而通过路由按任务加载必要模块。

预期核心引擎：

1. Intent Router
2. Reference Image Router
3. Identity Engine
4. Composition Engine
5. Beauty Retouch Engine
6. Lighting Engine
7. Photography Physics Engine
8. Prompt Compiler
9. Model Adapter
10. Quality Gate
11. Failure Diagnosis / Retry Planner

## 8. 修复验收标准

修复阶段至少满足：

- 全仓库不存在未声明的重复 Skill name。
- canonical 与 distribution mirror 的语义漂移可被 CI 自动发现。
- 人物身份、用户命令、安全边界、风格、构图、光影、美颜有唯一优先级契约。
- “医美级自然精修”有明确允许项与禁止项。
- “自动构图”区分 preserve / recompose。
- “完美光影”区分 relight / preserve-source。
- batch count 有唯一解析规则。
- V2.6 / V2.6.1 有明确版本映射。
- 人物专属锚点从通用规则层隔离。
- 历史图片 Prompt 默认不具有规则权威性。
- 外部 Skill 在许可不明时不直接 vendor。
- 新增自动校验，可阻止重复、版本漂移和镜像漂移再次进入主分支。

## 9. 本报告的权威状态

本文件是修复工程的 Baseline Inventory。后续所有修改需要能追溯到本报告中的一个问题编号或新增记录。任何删除动作都必须等价地保留可追溯历史，优先使用 deprecate、archive、redirect、generated mirror 和 CI gate，避免破坏已有调用链。
