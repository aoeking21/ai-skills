# wechat-miniprogram-builder

面向微信小程序全生命周期的可安装 Agent Skill。它把原仓库中分散的选题、开发、变现、审核、推广与矩阵经验，重构为可执行的产品与工程工作流，并增加运行时规则核验、安全架构、隐私一致性和审核修复协议。

当前版本：`1.0.0`。

## 主要能力

- 将模糊想法压缩成单一核心闭环和 MVP。
- 评估主体、类目、资质、数据、支付与广告边界。
- 生成微信原生小程序的页面、数据、状态和开发计划。
- 组织 AI 编程提示词、错误诊断和回归测试。
- 设计云开发、AI 接入与密钥安全方案。
- 处理上传、审核驳回、版本说明和发布检查。
- 设计合规冷启动、数据实验和产品组合策略。
- 对所有易变化的平台数字执行官方运行时核验。

## 安装

把本目录加入支持 Agent Skills 的客户端即可。并入 `aoeking21/ai-skills` 后，可使用：

```bash
npx skills add aoeking21/ai-skills --skill wechat-miniprogram-builder -g -a codex -y
```

临时调用：

```bash
npx skills use aoeking21/ai-skills --skill wechat-miniprogram-builder --agent codex
```

ChatGPT 工作区具备 Skills 上传功能时，可直接上传本目录的 ZIP 包。

## 基础调用

```text
使用 wechat-miniprogram-builder。
我想做一个给工地班组使用的记工小程序。先完成选题验证、MVP 范围、页面地图、数据结构和开发任务拆分，不接支付和广告。
```

```text
使用 wechat-miniprogram-builder。
这是微信开发者工具的报错和复现步骤。先定位根因，只给最小修复、改动文件和回归测试。
```

```text
使用 wechat-miniprogram-builder。
这是审核驳回意见。按事实、规则、触发页面、根因、最小修改、证明材料和版本说明输出整改方案。
```

## 文件结构

```text
wechat-miniprogram-builder/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── manifest.json
├── references/
│   ├── 00-runtime-verification.md
│   ├── 01-product-strategy.md
│   ├── 02-account-compliance.md
│   ├── 03-build-debug.md
│   ├── 04-cloud-ai-security.md
│   ├── 05-review-release.md
│   └── 06-growth-portfolio.md
└── assets/
    ├── project-brief-template.md
    ├── prompt-recipes.md
    ├── release-checklist.md
    └── review-repair-template.md
```

## 设计变化

本版保留原项目的阶段路由、提示词模板和上线检查思想，同时做了以下重构：

- 将固定费用、固定门槛、固定审核时间、固定分成和指定模型推荐移出核心规则。
- 增加官方运行时核验协议和时间锚点。
- 将“快速赚钱”和“批量铺量”改写为基于真实指标的产品实验。
- 增加服务端密钥、权限最小化、AI 内容治理和隐私一致性要求。
- 增加审核驳回的证据化修复流程。

## 来源与许可

本 Skill 派生自 `chenjin-cmd/wechat-miniprogram-builder`，上游采用 MIT License。重构版本由 `aoeking21` 维护，继续采用 MIT License。完整声明见 `NOTICE.md` 和 `LICENSE`。
