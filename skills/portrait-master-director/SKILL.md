---
name: portrait-master-director
description: 通用授权成人人像总控。用于以上传原图锁定当次身份、隔离可选人物 Reference Profile，并在任务允许重打光时调用专业光影适配器；不用于内置某个固定人物或跨任务默认复用个人照片。
metadata:
  version: "0.1.0"
---

# Portrait Master Director

把本轮上传的授权成年人原图作为默认且唯一的身份来源。系统本身不内置任何人物身份图片，也不把历史成片、AI 生成图或私人影集自动升级为身份真值。

## 固定边界

- 无人物预设：全局运行索引中的身份图片必须为 0。
- 当次身份：需要保持同一人时，优先使用本轮上传的真实原图。
- Profile 隔离：只有用户本轮显式选择 Profile 时才读取；不得根据姓名、相似脸或历史任务自动加载。
- 身份权威：只有用户确认的真实原始照片可标记为 `verified`；`model_generated` 永远是 `none`。
- 私人影集：原文件只读保存，默认退出运行索引；不删除、不移动、不改名。
- 既有治理：不得修改或绕过现有路由、安全、授权、任务模式和回退配置。

涉及资产录入、去重或 Canonical 状态时，读取 [资产治理合同](references/asset-governance.md)。涉及人物专属参考时，读取 [Reference Profile 合同](references/reference-profile-contract.md)。资产如何进入本轮任务由 [Reference Asset Router](references/reference-asset-router.md) 决定。

## 工作流

1. 判定任务是否要求身份保持，并确认人物为成年人且图像使用已获授权。
2. 将本轮上传图设为 `current_upload`。若缺少身份图，不得从历史影集静默补图。
3. 仅当用户显式指定 Profile 时加载该 Profile，并先验证来源、身份权威和人物隔离范围。
4. 用 Reference Asset Router 将当前上传图与 Profile 引用解析为角色化路由计划；被去重或拒绝的引用不得注入任务。
5. 继续沿用现有总优先级：安全与授权、用户本轮明确要求、身份不变量、摄影物理、构图/光影/美颜、默认风格。
6. 原片修复、4K 修复、保留现场或 `preserve-source` 任务禁止外部重打光适配器改变主光、背景、姿态或构图。
7. 用户明确要求伦勃朗光且任务允许 `relight` 时，读取 [Rembrandt External Adapter](references/rembrandt-external-adapter.md)，只委托光影域。
8. 输出应记录身份来源、显式 Profile 选择、任务模式、允许变更域、路由计划和实际适配器；不得把一次任务结果永久写回人物 Profile。

## 失败处理

- Profile 未显式选择、来源不明或引用 AI 生成图：拒绝其身份用途，继续使用本轮上传图。
- `preserve-source` 与重打光请求冲突：保留原光源逻辑，不调用 Rembrandt Adapter。
- 外部 Skill 未安装或不可用：返回可诊断的 `external_adapter_unavailable`，不得静默改走另一种光影风格。
- 逐图哈希证据缺失：标为 `unverified_hold`，不得根据文件大小推断重复。

部署、撤销或恢复该层时，读取 [回滚说明](references/rollback.md)。
