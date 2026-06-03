# Default Output Template

If the user provides a previous weekly report, mirror that format first.

Otherwise use this default Chinese structure:

```text
本周工作内容
  合并本人 PR <N> 个，协同推进/合入 <M> 个团队 PR，创建并推进 <I> 个 issues（其中 <CI> 个已关闭、<OI> 个持续中），提交 <C> 个 commits，覆盖以下工作线：
  1. <工作线 A>
  - <具体动作 1>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <具体动作 2>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <当前状态>：<仍 open 的 issue / PR，或下一步推进点>
  2. <工作线 B>
  - <具体动作 1>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <具体动作 2>：<做了什么>，<解决了什么问题 / 带来什么结果>
```

Grouping heuristics:

- CI / Workflow / Runner / Release
- Runtime / OpenCode / LLM / MCP
- Infra / Docker / K8s / Daytona / SWR
- Docs / Runbook / Design / Planning
- Collaboration / Merge / Repo maintenance

Writing rules:

- Prefer outcome-oriented bullets over commit-by-commit narration.
- Default to a report that is `细节足够、但还能直接贴进周报`，不要一上来就压成只有标题级概括。
- Each workstream should usually have `3-5` bullets when there is enough activity; fewer only when the topic is genuinely small.
- Each bullet should尽量同时回答两件事：`做了什么`，`为什么重要 / 解决了什么问题`。
- Collapse serial fix PRs into one workstream when they clearly belong to the same chain.
- Mention open issues or unmerged PRs in a short status line under the relevant workstream.
- If a collaborative PR includes one or two commits from the user, keep it under `协同推进/合入`, not `本人主线`.
- Prefer natural Chinese over mixed Chinese-English commit wording.
- Rewrite internal jargon into plain language whenever the meaning can be preserved.
- Prefer concrete subjects over generic summaries.
- Good: `将 PR checks 和 CodeQL 切到自托管 runner，减少公共 runner 排队和环境不一致导致的失败`
- Bad: `持续处理 CI 稳定性问题`
- Good: `搭建可复现的 Docker 验证环境，避免结果只在本机成立`
- Bad: `构建 reproducible Docker eval 环境，支撑 guarded canary rollout`
- Good: `补齐灰度验证和诊断能力，继续推进上线前保护措施`
- Bad: `新增 guarded canary、diagnostics、replay、rollout guard`
