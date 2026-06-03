---
name: issue-driven-development
description: Use when starting a non-trivial feature, integration, architecture change, bugfix investigation, or follow-up development request that should be researched, tracked in GitHub, and implemented from an issue-scoped branch.
---

# Issue-Driven Development

## Overview

Use this workflow to keep new work traceable and hard to derail: isolate work on a branch, research before coding, create or update a GitHub issue as the durable spec, then implement against that issue.

Core rule: never modify `main` directly.

## Workflow

1. **Check git state**
   - Run `git branch --show-current` and `git status --short --branch`.
   - If on `main` or `master`, create/switch to a new branch before any edits.
   - Use branch prefixes by intent: `docs/` for research-only, `feat/` for feature work, `fix/` for bug fixes.
   - Do not overwrite or revert unrelated dirty work.

2. **Research first**
   - Read the relevant repo code, docs, tests, and external primary sources when the request depends on current external behavior.
   - Write down assumptions, risks, alternatives, and open questions.
   - For integrations, identify lifecycle boundaries: where auth lives, where state lives, what can sleep/restart, how retries work, and what owns user-visible responses.

3. **Produce a durable research note when useful**
   - For substantial or ambiguous work, add a concise document under the project `docs/` directory.
   - Include the recommended approach, rejected approaches, operational risks, and concrete next development tasks.
   - Keep research commits separate from implementation commits when practical.

4. **Create or update a GitHub issue before implementation**
   - The issue is the implementation anchor. Include:
     - problem/background
     - goals and non-goals
     - recommended architecture or fix
     - data/API/session implications
     - acceptance criteria
     - target branch name
     - links to research docs and source references
   - If `gh` is available, create/read back the issue with `gh issue create` and `gh issue view`.
   - If `gh` auth/network is unavailable, provide a ready-to-paste title/body and continue only after the user creates or approves it.

5. **Start implementation from an issue-scoped branch**
   - Use a `feat/` or `fix/` branch named after the issue or core capability.
   - Keep the issue number and research doc in mind as the task context.
   - If the work starts from a research branch, branch from the research commit when that preserves useful context.

6. **Plan and implement in slices**
   - Break work into small, testable milestones.
   - For behavior changes, follow TDD: failing test first, minimal implementation, green test, then refactor.
   - Prefer mock/adapters around unstable external services so core platform behavior can be tested without live credentials.
   - Commit meaningful slices with focused messages.

7. **Verify before claiming progress**
   - Run focused tests for touched behavior.
   - Run typecheck/lint/build where appropriate.
   - If broader verification fails due unrelated existing issues, report the exact command and distinguish new vs pre-existing failures.
   - Check `git status --short --branch` before final response.

8. **Keep the issue updated**
   - Reference commits/branches in the issue or final response.
   - Note remaining open tasks and risks.
   - Do not merge or close the issue unless the user asks and verification supports it.

## GitHub Issue Template

```markdown
## Background

<Why this matters and what triggered the work.>

## Goals

- <User-visible or system outcome>
- <Operational constraint>

## Non-goals

- <Explicitly excluded scope>

## Recommended Approach

<Architecture or fix summary.>

## Acceptance Criteria

- [ ] <Observable behavior>
- [ ] <Test or verification condition>

## References

- <Research doc path>
- <Related issue/PR/source>

## Implementation Branch

`feat/<name>` or `fix/<name>`
```

## Common Mistakes

- Starting edits on `main`.
- Treating chat history as the only spec instead of creating an issue.
- Creating a branch but skipping research, then discovering lifecycle/auth/state constraints late.
- Letting a proof-of-concept become production architecture without documenting its limits.
- Claiming completion without fresh verification evidence.
