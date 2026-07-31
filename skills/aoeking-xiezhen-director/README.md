# aoeking-xiezhen-director

面向授权成年人物长期写真项目的 Agent Skill。重点解决人物身份漂移、身体比例漂移、摆拍感、事件缺失、衣料和环境物理失真，以及多张变体高度重复的问题。

当前版本：`1.2.0`。

## 安装到 Codex

```bash
npx skills add aoeking21/ai-skills --skill aoeking-xiezhen-director -g -a codex -y
```

也可以直接从目录安装：

```bash
npx skills add https://github.com/aoeking21/ai-skills/tree/main/skills/aoeking-xiezhen-director -g -a codex -y
```

查看仓库中可安装的 Skills：

```bash
npx skills add aoeking21/ai-skills --list
```

临时调用而不安装：

```bash
npx skills use aoeking21/ai-skills --skill aoeking-xiezhen-director --agent codex
```

## 基础调用

```text
使用 aoeking-xiezhen-director。
以上传照片中的成年女性为唯一身份参考，生成长沙盛夏强风街头纪实的完整提示词。强调人物 DNA 锁定、真实摄影事件、无摆拍、无持续镜头交流、衣料受力和自然出汗。
```

安装完成后，兼容客户端可根据任务自动激活该 Skill；支持显式 Skill 选择或 @ 提及时，也可直接选中 `aoeking-xiezhen-director`。

## GPT Image 2 专用 Adapter

Skill 内置 [`adapters/gpt-image-2.md`](adapters/gpt-image-2.md)，用于：

- 把人物写真规则编译成 `gpt-image-2` 专用提示词。
- 在纯文本生成与授权参考图编辑之间选择正确路由。
- 输出 Image API 参数包。
- 把 9:16、3:4 等画幅转换为有效尺寸。
- 为多张独立成片生成逐次调用计划。
- 修正 `input_fidelity`、透明背景和无效分辨率等参数错误。

### 只输出 GPT Image 2 提示词

```text
使用 aoeking-xiezhen-director 和 GPT Image 2 专用 Adapter。
以上传照片中的成年女性为唯一身份参考，生成 9:16 长沙强风街头纪实提示词。只输出可复制的最终提示词。
```

### 输出提示词与 API 参数

```text
使用 aoeking-xiezhen-director 和 GPT Image 2 专用 Adapter。
基于上传的授权成年人物参考图，生成 9:16 海边动态抓拍。
输出完整提示词和 OpenAI Image API 参数包。
```

参考图任务会使用 `edit` 路由并省略 `input_fidelity`。9:16 默认映射为 `1152x2048`，最终写真默认使用 `quality: high`、`output_format: png` 和 `n: 1`。

### 五张独立图片

```text
使用 aoeking-xiezhen-director 和 GPT Image 2 专用 Adapter。
生成五张同系列独立人像。每张使用不同摄影事件、动作阶段和构图。
输出五条完整提示词与五次独立 API 调用计划，严禁五宫格。
```

## ChatGPT

ChatGPT 的个人 Skills 可用性取决于套餐和工作区权限。具备 Skills 上传权限时，可将本目录打包为 ZIP，在 ChatGPT 的 Skills 页面选择上传。

## 来源与许可

本 Skill 的增强层由 aoeking21 维护，采用 MIT License。摄影提示词基础方法派生自 `nuyoah-ai-works/nuyoah-xiezhen-prompt`，上游版权和许可证见 `THIRD_PARTY_LICENSE` 与 `NOTICE.md`。

GPT Image 2 Adapter 于 2026-08-01 依据 OpenAI 官方模型页、Image generation 指南和 GPT Image prompting guide 校准。
