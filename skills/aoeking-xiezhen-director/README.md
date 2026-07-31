# aoeking-xiezhen-director

面向授权成年人物长期写真项目的 Agent Skill。重点解决人物身份漂移、身体比例漂移、摆拍感、事件缺失、衣料和环境物理失真，以及多张变体高度重复的问题。

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

## 调用示例

```text
使用 aoeking-xiezhen-director。
以上传照片中的成年女性为唯一身份参考，生成长沙盛夏强风街头纪实的 GPT Image 完整提示词。强调人物 DNA 锁定、真实摄影事件、无摆拍、无持续镜头交流、衣料受力和自然出汗。
```

安装完成后，兼容客户端可根据任务自动激活该 Skill；支持显式 Skill 选择或 @ 提及时，也可直接选中 `aoeking-xiezhen-director`。

## ChatGPT

ChatGPT 的个人 Skills 可用性取决于套餐和工作区权限。具备 Skills 上传权限时，可将本目录打包为 ZIP，在 ChatGPT 的 Skills 页面选择上传。

## 来源与许可

本 Skill 的增强层由 aoeking21 维护，采用 MIT License。摄影提示词基础方法派生自 `nuyoah-ai-works/nuyoah-xiezhen-prompt`，上游版权和许可证见 `THIRD_PARTY_LICENSE` 与 `NOTICE.md`。
