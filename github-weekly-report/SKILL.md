---
name: github-weekly-report
description: Use when the user asks for a weekly report, work log, status update, or GitHub activity summary of their recent development work. Ideal when the report should default to the last 7 days, infer the GitHub organization from the current repository, infer the user from the current gh login, and summarize PRs, issues, commits, and collaboration into a ready-to-paste status update.
---

# GitHub Weekly Report

## Overview

Use this when the user wants a work log or status report from GitHub activity instead of a raw list of commits. Default to the last 7 days unless the user gives a different range.

## Defaults

- Time window: last 7 calendar days ending today unless the user specifies dates.
- Scope: infer the GitHub owner from the current repo's `origin`. If it is an organization, search that org. If it is a user-owned repo, search that owner.
- User identity: start with the active `gh` login, then enrich with `gh api user`, local `git config user.name`, local `git config user.email`, and matching author aliases seen in local repos.
- Repos: search the owner broadly with `gh`, then inspect any checked-out sibling repos under the same workspace root that belong to the same owner.

## Workflow

1. Check GitHub auth with `gh auth status`.
2. If sandboxed `gh` says the token is invalid but the user says `gh` works locally, rerun the same command outside the sandbox and use that result.
3. Resolve the owner from `git remote get-url origin` first. If that fails, try `gh repo view --json owner,nameWithOwner`.
4. Resolve the user from `gh api user`. Do not depend on `user/emails`; many tokens do not have that scope.
5. Run `scripts/collect_github_weekly_activity.py` to gather:
   - authored PRs
   - involved PRs
   - authored issues
   - involved issues
   - authored commits from GitHub search
   - local git commits and mainline merges from sibling repos in the same owner
6. Deduplicate by `repo + number` for PRs/issues and by SHA for commits.
7. Write the report in the user's preferred format. If the user provides a prior weekly report, mirror that structure. Otherwise use the default template in `references/output-template.md`.

## Output Rules

- Separate `本人主线` from `协同合入/推进` when authorship is mixed.
- Count authored PRs and open PRs separately.
- Count commits from the deduplicated union of GitHub commit search and local git matches.
- Do not claim reviews, comments, or merges that you cannot verify from `gh` or local git history.
- Use concrete dates when the user refers to relative time like `上周四` or `今天`.
- If only local git data is available, say so explicitly.
- Prefer plain Chinese that a teammate can understand quickly without reading commit subjects one by one.
- Default to outcome-oriented wording first, implementation detail second.
- Default to `中等偏细` detail, not high-level slogans. A good first draft should usually make each workstream understandable without opening GitHub.
- For each workstream, prefer `3-5` bullets when the data supports it.
- Each bullet should usually contain both halves: `做了什么` and `解决了什么问题 / 带来什么结果`.
- Name the concrete subsystem, workflow, or component whenever possible. Prefer `把 PR checks 和 CodeQL 切到自托管 runner，减少公共 runner 排队` over `持续优化 CI 稳定性`.
- When a chain of commits clearly belongs to one topic, collapse it into one workstream, but keep the important steps visible instead of over-compressing into one vague sentence.
- If issues or PRs remain open, add a short `当前状态` bullet under the relevant workstream instead of burying that information in the summary line.
- Prefer reports that can be pasted directly into a weekly log with minimal editing. Do not spend the first draft on process narration or raw data dumps unless the user asks for them.
- Translate or compress internal jargon when possible. For example, prefer `灰度验证` over `guarded canary`, `回放验证` over `replay`, `诊断信息` over `diagnostics`, and `上线前保护措施` over `rollout guard`.
- If a technical English term must remain, explain it in the same bullet with simple Chinese instead of stacking raw jargon.
- Collapse long chains of related fixes into one understandable workstream. Do not echo every script or helper name unless it is important for understanding the result.

## Resources

- `scripts/collect_github_weekly_activity.py`: collects raw GitHub and local git activity into structured JSON.
- `references/output-template.md`: default Chinese weekly report structure and grouping heuristics.
