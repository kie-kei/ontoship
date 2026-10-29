---
name: dev-flow
description: The spec-driven development loop for preparing a feature/fix fast and safely on top of a GitMark KB — research → tasks → goal → spec (markdown via skills) → isolated git worktree → implement → tests → independent review → dev-tests → acceptance-tests → ship (diff, commits or PR). Use when starting a feature or fix, or when asked "how do we build/ship a change here".
---

# dev-flow — from idea to a verified change

A battle-tested loop for preparing a feature or fix with an AI agent. The spec is plain
**markdown written via the KB skills**, the work happens in an **isolated git worktree**,
and **only verified changes are ready for handoff**. The KB (see `kb-curate`) is the
carrier of knowledge — onboarding, hand-off and scaling all start from it, not from the
code. This flow ends with a prepared diff, commits or PR. Do not access production,
deploy, or merge as part of this flow.

## The loop

1. **Research** — understand from facts, not guesses: read logs, traces, and the code
   itself. Reproduce before fixing.
2. **Tasks** — turn the research into a list of tracked tasks with dependencies. Nothing
   gets lost.
3. **Goal** — crystallize one clear goal and the "done" criterion from those tasks.
4. **Spec** — write it as markdown in the KB via **`kb-curate`** (ontology: `node_type`,
   frontmatter, typed links `links.documents: [src/…]`). The spec is durable knowledge,
   not a throwaway ticket — searchable, linkable, graphable.
5. **Isolate** — work in a dedicated **`git worktree`**: `main` stays untouched, parallel
   agents don't collide, and rollback is just dropping the worktree.
6. **Implement** — code to the spec inside the worktree; keep doc↔code linked
   (`implemented_by`).
7. **Tests** — write/adjust unit + E2E for the feature. The test is part of the feature,
   not an afterthought.
8. **Independent review** — run an **independent model** (e.g. Codex CLI, read-only) over
   the diff for logic and security bugs before handoff. A second model catches what the
   author's model misses — on a real production codebase this pass caught **191 bugs**
   before they reached prod.
9. **Dev-tests** — run the full suite **locally or in CI**; no dedicated `dev` branch is
   required. Red → fix in the worktree and rerun. Record commands and results.
10. **Acceptance-tests** — run E2E/smoke scenarios in a **local test environment** against
    the spec's "done" criteria. Record the setup, commands and results so the checks are
    reproducible. Red → fix in the worktree and rerun.
11. **Ship** — update the KB to match the implementation, then hand off a **prepared diff,
    commits or PR** according to the task and project conventions; default to a prepared
    diff if no delivery form is specified. Report the changes, checks and remaining
    limitations. Done = criteria met, tests and independent review passed, documentation
    updated. Unresolved gates mean the work is incomplete.

## Git-flow

```
git worktree  →  diff + review  →  dev-tests (local / CI)  →  acceptance-tests (local)  →  diff / commits / PR
```

## Principles

- **Spec = markdown + skills.** No ceremony, but ontological — so it stays searchable,
  linkable and graphable (`kb-search` / `gitmark map`).
- **Worktree isolation by default** — clean parallelism and clean rollback.
- **Tests and independent review are gates, not afterthoughts.**
- **Verify with reproducible checks** against the spec's "done" criteria.
- **md + git = source of truth**; everything derived (search index, graph) is regenerated.

## When to apply

Starting any non-trivial feature or fix. For a one-line change you can collapse steps,
but keep the gates (review + tests) — they are where the 191 bugs were caught.
