# AI Skills Library

张霆的个人 AI Skills 总库，用于集中管理图像生成、提示词工程与 Agent 工作流。

## 图像生成

### female-portrait-director

女性人像提示词导演 Skill：锁定用户明确参数，通过单一路由组织人物、动作、服装、场景、镜头、光线与滤镜，生成完整、可复制的摄影导演式提示词；支持已授权成年人物或产品参考主体的保留工作流。

- [进入模块](image-generation/female-portrait-director/README_zh.md)
- [Skill 入口](image-generation/female-portrait-director/SKILL.md)
- [独立仓库](https://github.com/aoeking21/female-portrait-director)
- 上游来源：[liyue-aigc/female-portrait-director](https://github.com/liyue-aigc/female-portrait-director)

<!-- nuyoah-xiezhen-prompt:start -->

### nuyoah-xiezhen-prompt

南鸢写真提示词 Skill 的锁定上游镜像，以及面向长期人物项目的 aoeking 增强层。

- [模块入口](image-generation/nuyoah-xiezhen-prompt/README.md)
- [上游原版](image-generation/nuyoah-xiezhen-prompt/upstream/SKILL.md)
- [aoeking 增强版](image-generation/nuyoah-xiezhen-prompt/aoeking-enhanced/SKILL.md)
- 上游来源：[nuyoah-ai-works/nuyoah-xiezhen-prompt](https://github.com/nuyoah-ai-works/nuyoah-xiezhen-prompt)

<!-- nuyoah-xiezhen-prompt:end -->

## 目录结构

```text
ai-skills/
├── image-generation/
│   ├── female-portrait-director/
│   └── nuyoah-xiezhen-prompt/
├── prompt-engineering/
└── docs/
```

## 许可与署名

- `female-portrait-director` 保留原项目作者、许可证、免责声明和版本信息。该模块使用 MIT License。
- `nuyoah-xiezhen-prompt/upstream` 保留南鸢 nuyoah 的原始版权、来源、版本清单和 MIT License；`aoeking-enhanced` 作为独立增强层维护。