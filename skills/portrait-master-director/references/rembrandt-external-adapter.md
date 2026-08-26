# Rembrandt External Adapter V1

## 外部来源

- Repository：`okooo5km/rembrandt-portrait-lighting`
- 已核对提交：`28fc5e579142a37179e2443fdb17d17fb90248d6`
- 许可证状态：`UNVERIFIED`（仓库根目录未提供可识别许可证）
- Vendoring：许可证明确前禁止复制外部 Skill 正文、图片和提示词资产

该仓库是新近发布的单一专项实现，当前只作为外部能力候选，不作为本系统的规则权威。

## 激活条件

同时满足以下条件才可调用：用户明确要求伦勃朗光；`lighting_mode = relight`；任务不是原片修复、4K 修复、保留现场或 `preserve-source`；存在本轮上传的授权人物参考图。

## 委托边界

允许外部 Skill 返回主光方向、光比、负补光、克制轮廓分离、面部平面明暗组织，以及用户明确允许时的影棚背景光影建议。

禁止改变人物身份、年龄、脸型、五官比例、体型、独特特征、服装、人物数量与映射，以及未授权的姿态、机位、构图、场景、安全、路由或回退。

外部结果必须声明 `changed_domains`。Adapter 只接受 `lighting`，以及用户明确允许影棚转换时的 `background`；出现其他域即拒绝。

## 失败和回退

- 未安装：`external_adapter_unavailable`
- 激活条件不满足：`not_applicable`
- 外部返回越权：`external_adapter_scope_violation`
- 不得把失败静默替换成其他风格；上层可保持原光影并报告。
