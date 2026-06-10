# Default Output Template

If the user provides a previous weekly report, mirror that format first.

Otherwise use this default Chinese structure:

```text
本周工作内容
  合并本人 PR <N> 个，协同推进/合入 <M> 个团队 PR，创建并推进 <I> 个 issues（其中 <CI> 个已关闭、<OI> 个持续中），提交 <C> 个 commits，覆盖以下工作线：
  1. <工作线 A>
  - <具体动作 1>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <具体动作 2>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <当前状态>：<仍未关闭的 issue / 未合并的 PR，或下一步推进点>
  2. <工作线 B>
  - <具体动作 1>：<做了什么>，<解决了什么问题 / 带来什么结果>
  - <具体动作 2>：<做了什么>，<解决了什么问题 / 带来什么结果>
```

Grouping heuristics:

- 持续集成 / 工作流 / 自托管执行机 / 发布
- 运行时 / OpenCode / LLM / MCP / 模型调用
- 基础设施 / Docker / K8s / Daytona / SWR
- 文档 / 操作手册 / 方案设计 / 规划
- 协作合入 / 仓库维护

Writing rules:

- Prefer outcome-oriented bullets over commit-by-commit narration.
- Default to a report that is `细节足够、但还能直接贴进周报`，不要一上来就压成只有标题级概括。
- Each workstream should usually have `3-5` bullets when there is enough activity; fewer only when the topic is genuinely small.
- Each bullet should尽量同时回答两件事：`做了什么`，`为什么重要 / 解决了什么问题`。
- Collapse serial fix PRs into one workstream when they clearly belong to the same chain.
- Mention open issues or unmerged PRs in a short status line under the relevant workstream.
- If a collaborative PR includes one or two commits from the user, keep it under `协同推进/合入`, not `本人主线`.
- Prefer natural Chinese over mixed Chinese-English commit wording.
- Keep GitHub metric labels such as `PR`, `issues`, and `commits` in English when they make the count clearer; use Chinese for the surrounding narrative.
- Keep exact identifiers in English when they are repository names, branch names, commands, API paths, model names, product names, protocol names, or established acronyms such as `GitHub`, `OpenCode`, `LLMLingua2`, `DCP`, `Qwen`, `Docker`, `Kubernetes/K8s`, `Daytona`, `SWR`, `GHCR`, `CI`, `API`, `LLM`, and `MCP`.
- Translate generic technical terms for leaders and non-implementers: `worker` -> `工作服务`, `provider` -> `供应方`, `contract` -> `接口约定` or `契约`, `context` -> `上下文`, `workflow` -> `工作流`, `runner` -> `执行机`, `runbook` -> `操作手册`, `backlog` -> `待办`, `rollout` -> `上线` or `发布`.
- Rewrite internal jargon into plain language whenever the meaning can be preserved.
- Prefer concrete subjects over generic summaries.
- Good: `将 PR 校验和 CodeQL 切到自托管执行机，减少公共执行机排队和环境不一致导致的失败`
- Bad: `持续处理 CI 稳定性问题`
- Good: `搭建可复现的 Docker 验证环境，避免结果只在本机成立`
- Bad: `构建 reproducible Docker eval 环境，支撑 guarded canary rollout`
- Good: `补齐灰度验证和诊断能力，继续推进上线前保护措施`
- Bad: `新增 guarded canary、diagnostics、replay、rollout guard`
- Good: `新增远端压缩工作服务，并说明失败时放行的保护边界`
- Bad: `新增 remote compression worker 和 fail-open guard`
