---
description: Run the OntoShip dev-flow — take a feature/fix from idea to a verified diff, commits or PR through the gated pipeline (research → tasks → goal → spec → worktree → implement → tests → review → dev-tests → acceptance-tests → ship).
---

Drive the change described in `$ARGUMENTS` through the **OntoShip dev-flow**.

This flow ends at handoff. Do not access production, deploy, or merge as part of it.

Follow the `dev-flow` skill end to end:

1. **Research** — understand from facts (logs, traces, code); reproduce before fixing.
2. **Tasks** — decompose into tracked tasks.
3. **Goal** — crystallize one clear goal + "done" criterion.
4. **Spec** — write it as markdown in the KB via `kb-curate` (node_type, frontmatter,
   typed links `documents:[src/…]`). Search the KB first (`kb-search`) — don't duplicate.
5. **Isolate** — work in a dedicated `git worktree`.
6. **Implement** — code to the spec.
7. **Tests** — write/adjust unit + E2E.
8. **Independent review** — run an independent model (e.g. Codex CLI, read-only) over the diff.
9. **Dev-tests** — run the full suite locally or in CI, without requiring a `dev` branch.
   Red → fix in the worktree and rerun. Record commands and results.
10. **Acceptance-tests** — check the spec's "done" criteria with E2E/smoke in a local test
    environment. Record the setup, commands and results. Red → fix and rerun.
11. **Ship** — update the KB to match the implementation; hand off a prepared diff, commits
    or PR according to the task and project conventions. Default to a prepared diff if no
    delivery form is specified. Report changes, checks and remaining limitations.

Keep the gates (tests + independent review). Don't skip the spec — it's the carrier of
knowledge, not a throwaway ticket. Done = criteria met, tests and independent review
passed, documentation updated. Unresolved gates mean the work is incomplete.
