# Quality Gate and Auto-Repair V1

Quality Gate 在输出交付前逐域校验，失败时进入有界自动返修；不通过绝不静默放行。

## 校验域

每个输出必须声明：

- `identity_source`：身份保持任务必须声明来源（通常是 `current_upload`）。
- `changed_domains`：实际变更的域，必须全部落在请求的 `allowed_changes` 内。
- `safety_reviewed`：必须为 `true`，否则拒绝。

受保护域（`identity`、`age`、`face_geometry`、`body_proportions`、`distinctive_features`、`subject_count`、`subject_mapping`、`clothing`、`safety`、`routing`、`fallback`）任何一项出现在 `changed_domains` 或对应 `*_changed` 声明中即判失败。

请求声明 `subject_count` 时，输出声明的数量必须一致。

## 自动返修

- 默认最多 `2` 轮，可通过 `max_repair_rounds` 配置，负数直接拒绝。
- 每轮向生产者传入 `repair_round` 与 `quality_gate_feedback`（`failing_domains` + `required_actions`）。
- 第 N 轮通过：状态 `passed`，记录 `repair_rounds = N`。
- 达到上限仍未通过：状态 `quality_gate_failed`，返回全部失败检查，不允许降级为通过。
- 无模型回退、无风格替换；上层可保持原输出并报告失败。

## 边界

该层只校验输出声明与任务约束，不调用外部适配器、不修改原图、不改变路由。未知检查域按数据错误处理，不得静默忽略。
