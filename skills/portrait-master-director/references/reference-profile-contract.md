# Reference Profile Contract V1.0

Reference Profile 是可插拔、按人物隔离的私有参考集合，不是全局精选图库。

## 路由规则

1. 本轮上传图始终是当次身份的主参考。
2. Profile 只有在用户本轮显式提供 `profile_id` 并允许加载时生效。
3. Profile 不能按姓名、相似脸、历史会话或文件名自动发现。
4. 一个 Profile 只能描述一个人物；多人任务需要独立 Profile 与屏幕位置映射。
5. Profile 只能补充当前上传图可见信息不足的明确特征，不能覆盖当前人物身份。

## 权威与用途

- `verified_identity`：用户确认的真实原始照片，可辅助同一人物身份连续性。
- `verified_feature`：用户确认的真实局部特征照片，例如纹身；只影响对应特征。
- `composition`、`lighting`、`style`：不具有身份权威。
- `model_generated`：禁止出现在身份或特征权威列表中。

Profile 存放在私有资产空间，仓库只提供 Schema。不得提交个人照片、绝对本地路径、面部嵌入、云盘令牌或可公开访问的签名 URL。一次任务对服装、体型修辞、妆容、场景和姿态的修改不得自动写回 Profile。
