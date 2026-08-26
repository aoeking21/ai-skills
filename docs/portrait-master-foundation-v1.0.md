# Portrait Master Foundation V1.0

## 决策

Portrait Master 是无人物预设的通用系统。身份保持任务默认只使用本轮上传的授权真实原图；系统不内置咪咪或任何其他人物的身份图片。

Canonical Reference 定义为可插拔、按人物隔离且必须显式选择的 Reference Profile 机制。Profile 存放在私有资产空间，不进入本仓库。

## 咪咪影集

- 普通脸部、身体和连续写真：只读归档，退出运行索引。
- 历史 AI 成片：不具有身份权威。
- 背部纹身参考：如需使用，只存在于仓库外私有 `mimi` Profile，并由用户本轮显式选择。
- 不删除、不移动、不重命名原图。

## External Lighting Adapter

Rembrandt External Adapter 只在用户明确要求、任务允许 `relight` 且存在本轮授权参考图时准备调用计划。外部结果只能改变允许的光影域；身份、年龄、人物映射、安全、路由和回退均受保护。

外部仓库许可证尚未确认，因此没有复制其 Skill 正文、图片或提示词资产。

## Reference Asset Router

Reference Asset Router 将本轮上传图与显式激活的 Profile 引用解析为角色化路由计划：当前上传始终是主身份来源；未显式激活的 Profile 不加载；`model_generated` 不携带身份或特征权威；命中 exact/visual 重复组的引用去重；`preserve-source` 与修复类任务禁用非权威参考。

## Manifest 状态

Portrait Master Runtime Manifest 已完成：全局可路由身份资产为 0，私人影集不进入运行记录。

Archive Audit 独立保存为汇总状态。上一轮逐图 SHA-256/感知哈希表未持久化到当前工作区；重新接入 `/咪咪的影集` 只读数据源后才能补齐私人归档审计。缺失记录不得从文件大小或旧摘要推断，该状态不阻塞通用系统。

## 回滚

本阶段仅新增独立 Skill、数据 Schema、校验脚本、测试和独立 CI。回滚时移除这些新增文件并停止调用新 Skill；既有路由、安全、回退和原始影集无需恢复。
