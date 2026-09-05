---
name: portrait-master-director
description: 通用授权成人人像总控。用于以上传原图锁定当次身份、强制执行人像摄影调用链、隔离可选人物 Reference Profile，并在任务允许重打光时调用专业光影适配器；不用于内置某个固定人物或跨任务默认复用个人照片。
metadata:
  version: "0.2.0"
---

# Portrait Master Director V0.2.0

把本轮上传的授权成年人原图作为默认且唯一的身份来源。系统本身不内置任何人物身份图片，也不把历史成片、AI 生成图或私人影集自动升级为身份真值。

## 强制激活与执行门

`portrait-master-director` 与“人像摄影”是本 Skill 的强激活词。用户在创建、编辑、重绘、修复或生成成人人像任务中显式使用任一激活词时，必须读取并执行 [Mandatory Invocation and Image Generation Contract](references/invocation-and-image-contract.md)。

强激活后不得把激活词仅作为普通风格描述，也不得在未实际读取本文件与任务所需 references 的情况下直接进入图像生成。生成前硬门任一必需检查失败时，必须停止并报告可诊断状态，禁止静默降级为普通原生出图。

用户询问“调用 Skill 了吗”时，只能依据本轮真实执行轨迹回答；仅识别到激活词不等于已经调用。

## 固定边界

- 无人物预设：全局运行索引中的身份图片必须为 0。
- 当次身份：需要保持同一人时，优先使用本轮上传的真实原图。
- Profile 隔离：只有用户本轮显式选择 Profile 时才读取；不得根据姓名、相似脸或历史任务自动加载。
- 身份权威：只有用户确认的真实原始照片可标记为 `verified`；`model_generated` 永远是 `none`。
- 私人影集：原文件只读保存，默认退出运行索引；不删除、不移动、不改名。
- 既有治理：不得修改或绕过现有路由、安全、授权、任务模式和回退配置。

涉及资产录入、去重或 Canonical 状态时，读取 [资产治理合同](references/asset-governance.md)。涉及人物专属参考时，读取 [Reference Profile 合同](references/reference-profile-contract.md)。资产如何进入本轮任务由 [Reference Asset Router](references/reference-asset-router.md) 决定。所有强激活图像任务必须读取 [Invocation and Image Contract](references/invocation-and-image-contract.md)。输出交付前按 [Quality Gate](references/quality-gate.md) 校验，失败进入有界自动返修。

## 三层执行架构

### L1 Governance

负责授权、身份来源、current_upload、Profile 隔离、Reference Asset Router、资产治理和受保护域。

### L2 Portrait Director

负责把用户要求转译为真实可执行的人像摄影任务合同，包括身份、身体约束、服装、动作、神态、构图、镜头、场景、天气、光影和摄影物理。具体规则由 Invocation and Image Contract 执行。

### L3 Execution Gate

负责强制读取、Task Contract 编译、Prompt Compiler、PRE_GENERATION_GATE、图像生成尝试与 POST_GENERATION QUALITY GATE。L3 未通过时禁止进入图像生成。

## 工作流

1. 识别强激活词。命中时立即读取 `references/invocation-and-image-contract.md`，设置 `MANDATORY_SKILL_TRIGGER=true`。
2. 判定任务是否要求身份保持，并确认人物为成年人且图像使用已获授权。
3. 将本轮上传图设为 `current_upload`。若缺少身份图，不得从历史影集静默补图。
4. 身份保持任务读取 `references/reference-asset-router.md`；仅当用户显式指定 Profile 时加载该 Profile，并先验证来源、身份权威和人物隔离范围。
5. 用 Reference Asset Router 将当前上传图与显式 Profile 引用解析为角色化路由计划；被去重或拒绝的引用不得注入任务。
6. 建立 Task Contract，至少解析 identity_source、subject_count、task_mode、scene、wardrobe、body_constraints、expression、pose_action、camera_composition、lighting_weather、photographic_style、protected_domains、allowed_changes、negative_constraints。
7. 继续沿用总优先级：安全与授权、用户本轮明确要求、身份不变量、摄影物理、构图/光影/美颜、默认风格。
8. 原片修复、4K 修复、保留现场或 `preserve-source` 任务禁止外部重打光适配器改变主光、背景、姿态或构图。
9. 用户明确要求伦勃朗光且任务允许 `relight` 时，读取 [Rembrandt External Adapter](references/rembrandt-external-adapter.md)，只委托光影域。
10. 运行 PRE_GENERATION_GATE。未通过则停止，不得调用图像生成器。
11. 通过 Prompt Compiler 将 Task Contract 编译为最终图像指令，然后才允许调用图像生成器。
12. 对候选输出运行 Quality Gate，并执行当前工具链可可靠完成的视觉检查：身份一致性、脸部几何、年龄观感、显著特征、人数、身体约束、服装、场景、动作、摄影真实感与解剖完整性。
13. 未通过时按 `quality_gate_feedback` 有界返修，默认最多 2 轮；仍不通过则返回 `quality_gate_failed`，不得静默降级。
14. 输出应记录身份来源、显式 Profile 选择、任务模式、允许变更域、路由计划、实际适配器、生成状态和质量门结果；不得把一次任务结果永久写回人物 Profile。

## 失败处理

- Skill 或必需 reference 未实际读取：`SKILL_NOT_LOADED` 或 `SKILL_LOADED_GATE_FAILED`，禁止出图。
- Profile 未显式选择、来源不明或引用 AI 生成图：拒绝其身份用途，继续使用本轮上传图。
- `preserve-source` 与重打光请求冲突：保留原光源逻辑，不调用 Rembrandt Adapter。
- 外部 Skill 未安装或不可用：返回可诊断的 `external_adapter_unavailable`，不得静默改走另一种光影风格。
- 逐图哈希证据缺失：标为 `unverified_hold`，不得根据文件大小推断重复。
- 无法可靠量化视觉相似度：标记 `not_measurable`，禁止伪造百分比、像素级或生物识别级验证结果。
- 图像生成器因安全或产品限制拒绝：保留 `SKILL_EXECUTED_GENERATION_ATTEMPTED` 事实并报告生成失败，禁止宣称已经成功出图。

部署、撤销或恢复该层时，读取 [回滚说明](references/rollback.md)。
