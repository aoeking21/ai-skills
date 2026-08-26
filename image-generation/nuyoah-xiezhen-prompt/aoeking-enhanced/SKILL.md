---
name: aoeking-xiezhen-legacy-bridge
description: 早期 aoeking 写真增强层的兼容入口。仅用于历史资料追溯、旧调用迁移与规则对照。新的授权成年真人写真任务统一使用仓库 canonical Skill `skills/aoeking-xiezhen-director`；本兼容层不得与正式 Skill 竞争路由优先级。
license: MIT
metadata:
  author: "aoeking21"
  version: "1.0.1"
  status: "deprecated"
  replaced_by: "skills/aoeking-xiezhen-director"
  derived_from: "nuyoah-ai-works/nuyoah-xiezhen-prompt@bc1edb21655e36b89599d31b16f23ad5193d483f"
---

# aoeking 写真导演 Legacy Bridge

## 状态

本目录保留早期增强版，目的只有三个：历史追溯、迁移兼容、与上游规则对照。

正式执行入口：[`../../../skills/aoeking-xiezhen-director/SKILL.md`](../../../skills/aoeking-xiezhen-director/SKILL.md)。

新的任务、文档、安装命令、Agent 路由和测试不得再把本文件声明为 `aoeking-xiezhen-director`。

## 历史能力摘要

早期版本已经建立三层结构：

1. 人物真值：授权成年人物的身份、真实年龄、身体结构与连续性。
2. 摄影事件：用真实事件因果推导重心、视线、表情、衣料、风、水与环境接触。
3. 成像表达：构图、机位、焦段、光线、皮肤纹理和负面约束。

这些原则已经被正式 `aoeking-xiezhen-director` 吸收和继续维护。

## 兼容规则

- 历史文档引用本目录时可以继续读取其中 references 进行对照。
- 发生规则冲突时，以正式 `skills/aoeking-xiezhen-director` 为准。
- 不在本目录新增 Adapter、Preset、Eval 或新的摄影规则。
- 不从本目录生成新的安装说明。
- 不删除本目录，以保证 Git 历史和旧链接可追溯。

## 迁移

旧调用：

```text
$aoeking-xiezhen-legacy-bridge
```

应迁移为：

```text
$aoeking-xiezhen-director
```

正式 Skill 已包含 GPT Image 2 Adapter、街头纪实预设、质量评测与失败诊断，后续能力统一在那里升级。
