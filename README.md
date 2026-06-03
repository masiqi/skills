# skills

这个仓库用于保存我自己日常使用、持续维护的 Codex skills。

目标是把常用的工作方法、自动化脚本和输出模板沉淀成可复用的 skill，后续可以单独演进，也方便在不同项目之间复用。

## 目录结构

每个 skill 都放在独立目录下，尽量自包含：

```text
<skill-name>/
  SKILL.md
  agents/
  references/
  scripts/
```

常见约定：

- `SKILL.md`：skill 的主说明文件，定义触发条件、默认行为和执行规则
- `agents/`：和 skill 配套的 agent 配置
- `references/`：输出模板、参考文档等静态资料
- `scripts/`：skill 依赖的辅助脚本

## 当前已收录 skills

### `github-weekly-report`

用于根据 GitHub 和本地 git 活动生成中文周报/工作日志，默认会：

- 从当前仓库推断 GitHub owner / org
- 从当前 `gh` 登录推断用户身份
- 默认统计最近 7 天的 PR、issue、commit 和协同合入情况
- 输出可直接粘贴到周报里的中文总结

### `issue-driven-development`

用于把较完整的开发任务按 issue 驱动方式推进，核心约束包括：

- 先研究，再落 issue
- 不直接在 `main` 上改
- 从 issue 对应分支开始实现
- 保留实现过程、验收标准和后续跟进信息

## 使用方式

如果要在本机使用这些 skill，可以按需复制到本地 skill 目录，例如：

```bash
cp -a github-weekly-report ~/.codex/skills/
cp -a issue-driven-development ~/.codex/skills/
```

也可以直接把整个仓库 clone 下来，再按需同步其中的 skill。

## 维护原则

- 每个 skill 尽量只解决一类明确问题
- 优先沉淀稳定、可复用的工作流，而不是一次性操作记录
- 有较大变更时，尽量通过 issue 和 PR 留下可追踪的上下文
