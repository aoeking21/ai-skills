# Rollback

本 Skill 是独立新增层，不替换现有 Skill，也不修改既有 Route、安全或回退配置。

## 回滚步骤

1. 停止调用 `portrait-master-director`，恢复直接调用原有写真导演或女性人像导演。
2. 从运行环境移除该 Skill 的安装入口或禁用新 CI 工作流。
3. 删除本分支新增的 `skills/portrait-master-director/`、测试工作流和对应文档提交。
4. 私有 Reference Profile 与原始影集保持不动，不需要数据迁移或恢复。

本层不改写原图、不保存个人图片、不生成面部嵌入，也不把任务结果写回 Profile。因此代码回滚不依赖资产回滚。
