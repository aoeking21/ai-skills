# Nuyoah 写真提示词模块

本目录采用“上游精确镜像 + 本地增强层”结构。

## 目录

- [`upstream/`](upstream/)：南鸢 `nuyoah-xiezhen-prompt` 的只读镜像，锁定提交见 [`UPSTREAM_COMMIT`](UPSTREAM_COMMIT)。
- [`aoeking-enhanced/`](aoeking-enhanced/)：面向长期人物写真项目的增强层，增加人物身份 DNA、真实摄影事件和失败诊断。

## 使用边界

上游文件保留原作者、来源和 MIT License。更新上游时应整体替换 `upstream/`，不要在镜像目录中直接维护私有改动。所有定制规则统一放入 `aoeking-enhanced/`，以降低上游升级冲突。

## 上游来源

- 项目：`nuyoah-ai-works/nuyoah-xiezhen-prompt`
- 锁定提交：`bc1edb21655e36b89599d31b16f23ad5193d483f`
- 上游版本：`0.1.0`
- 许可：MIT

<!-- canonical-skill:start -->

## 可安装标准 Skill

完全自包含的正式入口位于 [`skills/aoeking-xiezhen-director`](../../skills/aoeking-xiezhen-director/README.md)。该目录可以被 Agent Skills 客户端独立发现、安装和更新，不依赖本模块的相对路径。

```bash
npx skills add aoeking21/ai-skills --skill aoeking-xiezhen-director -g -a codex -y
```

<!-- canonical-skill:end -->
