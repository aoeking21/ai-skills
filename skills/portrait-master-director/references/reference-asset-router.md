# Reference Asset Router V1

Reference Asset Router 把本轮上传图和显式激活的 Profile 引用解析为角色化路由计划，供上层决定哪些资产参与身份约束、哪些只作为非权威风格参考、哪些被去重或拒绝。

## 路由输入

- `identity_reference`：本轮上传的真实原图，始终是主身份参考。
- `profile_id` + `profile_activation_explicit`：只有两者同时出现才读取 Profile。
- `task_mode`：`restoration`、`preserve_source`、`preserve` 禁止非权威参考影响输出。
- `allowed_changes`：决定 `composition`、`lighting`、`style` 参考是否启用。
- `known_duplicates`：`asset_id -> {exact_duplicate_group, visual_duplicate_group}`，来自 Visual Asset Manifest 的证据，不允许仅凭文件大小推断。

## 路由规则

1. 当前上传图总是 `identity_primary`，身份权威 `verified`。
2. 未显式激活 Profile 时，不加载任何历史资产。
3. `verified_identity`、`verified_feature` 只作为补充，不覆盖当前身份；没有当前上传时拒绝这两类引用。
4. `model_generated` 不能携带身份或特征权威；非权威角色（`composition`/`lighting`/`style`）允许但 `identity_authority` 必须为 `none`。
5. 与当前上传或已路由资产命中同一 exact/visual 重复组的引用直接去重，不重复注入。
6. 身份保持任务缺少当前上传图：拒绝整个路由（`GovernanceError`）。
7. 未知角色：拒绝整个路由（数据错误，不静默忽略）。
8. `preserve-source` / 修复类任务：非权威参考保持禁用，即使 `allowed_changes` 包含对应域。

## 输出

`routed`：每条含 `asset_id`、`role`、`source`（`current_upload`/`profile`）、`provenance`、`identity_authority`、`profile_id`、`enabled`、`reason`。

`rejected`：被拒绝的引用及原因；`deduplicated`：命中重复组而未注入的 `asset_id`。

该层只做资产路由，不调用外部适配器，也不修改原图。光影委托仍由 Rembrandt External Adapter 按自己的激活条件独立判断。
