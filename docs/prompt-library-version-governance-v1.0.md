# Prompt Library Version Governance V1.0

## 1. 当前确认的 Canonical Library

当前已确认存在正式主文件：

`AI图像生成提示词总库_V2.6_视觉命题关系场增强版.md`

其正式配套包括 V2.6 模块索引与简明激活表。

## 2. V2.6.1 的状态

近期历史成片和任务 Prompt 中多次出现“调用《AI图像生成提示词总库 V2.6.1｜视觉命题关系场增强版》”，但本轮盘点没有确认一个独立、可追溯、具有 changelog 的正式 `V2.6.1` 主文件。

因此从本治理版本起：

```text
V2.6.1 = deprecated runtime alias
canonicalize_to = V2.6
```

解释：V2.6.1 可能代表历史任务中叠加了若干局部补丁后的口头版本号，但在没有正式主文件和差异清单前，不能把它视为新的 Single Source of Truth。

## 3. Resolver 规则

当调用器、Agent、历史 Prompt 或小龙虾后续接入层收到：

```text
调用 V2.6.1
```

必须解析为：

1. 加载 V2.6 canonical master。
2. 解析当前任务明确点名的补丁，例如 identity lock、4K restoration、street documentary、wind physics、subject unique feature 等。
3. 加载 GitHub 当前 canonical Skill contracts。
4. 不通过“V2.6.1”这个字符串隐式加载未知规则。

## 4. 新版本发布规则

以后只有同时满足以下条件，才允许形成新的正式版本号：

- 有唯一主文件。
- 有 module index。
- 有 activation table 或 resolver mapping。
- 有 changelog，明确相对于上一个版本新增、删除、重构和废弃项。
- 有 canonical path。
- 通过重复、冲突、Skill name、版本和路由校验。

## 5. 历史资料

历史 V2.3 / V2.4 / V2.5 / V2.5.1 和含“V2.6.1”字符串的成片都保留用于追溯与评测，不作为当前最高规则。

历史文件不得直接删除。需要通过 archive/deprecated/alias 方式降级，防止旧链接和历史证据失效。
