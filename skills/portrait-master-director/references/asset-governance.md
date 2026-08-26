# Visual Asset Governance V1.0

Visual Asset Manifest 记录证据和路由资格，不对原图执行删除、移动、重命名或改写。原始影集与运行索引分离。

## 必需字段

每个可物化的资产记录至少包含 `asset_id`、来源路径、文件名、MIME、尺寸、字节数、SHA-256、感知哈希、两个重复组、来源、身份权威、Canonical 状态、Profile 范围和运行索引状态。

## 去重证据

- `exact_duplicate_group` 只能基于相同 SHA-256 建立。
- `visual_duplicate_group` 必须记录感知哈希或视觉特征算法、阈值和人工复核状态。
- 相同文件大小只能产生候选，不能产生重复结论。
- 无法读取的文件标为 `unverified_hold`。

## 身份证据

- `user_confirmed_real_original` 才有资格成为 `verified`。
- `provenance_unknown` 最多为 `candidate`，不得自动提升。
- `model_generated`、历史输出、风格图和合成图的 `identity_authority` 必须是 `none`。
- 任何人物身份参考必须属于独立 `profile_scope`，禁止 `global` 身份锚点。

## 咪咪影集决策

- 全局身份运行索引：0 张。
- 普通脸部、身体、连续写真：只读归档，退出运行索引。
- AI 生成图：`historical_output`，不参与身份路由。
- 背部纹身参考：仅可存在于仓库外的私有 `mimi` Profile，且必须由用户显式选择。
- 当前仓库不保存咪咪 Profile、图片路径、图片字节或生物特征嵌入。

当前 Manifest 的范围是 Portrait Master 可路由资产。由于私人影集全部退出运行索引，`asset_records` 为空且 Runtime Manifest 已完成。

私人影集的 Archive Audit 与运行 Manifest 分离。上一轮逐图 SHA/感知哈希表没有持久化到当前工作区，因此归档审计保持 `summary_only_requires_source_rehydration`；重新接入只读数据源后才可补齐，禁止从摘要反推单文件哈希。归档审计不影响 Portrait Master 运行。
