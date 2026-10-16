---
description: Search the project knowledge base via GitMark (FTS5 bm25 + trigram/fuzzy). Argument = query; no argument shows stat.
allowed-tools: Bash(python3:*)
---

Search the project's markdown knowledge base (all `.md`: docs/, README files, etc.).

User query: `$ARGUMENTS`

Do:
1. If `$ARGUMENTS` is empty — run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/kb-search/gitmark.py stat` and show the `/kb <query>` syntax.
2. If the question is **structural** — "which/how many docs are X", "what's deprecated",
   "what did an agent write that nobody verified", "plans per service" — answer with
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/kb-search/gitmark.py query <key=val …> [--count-by key]`
   instead of full-text search (see the kb-search skill for the condition syntax).
3. Otherwise:
   - Refresh the index if needed: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/kb-search/gitmark.py index`.
   - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/kb-search/gitmark.py search "$ARGUMENTS" -k 8`
   - Summarize the top hits (which files, `file:line`), don't reprint whole snippets. Open the 1–2 most relevant files and answer the question.
   - Nothing relevant? Retry once or twice with a reformulation (exact identifier, ru↔en, synonym) before concluding it isn't documented.
   - If a hit is marked `stale` or `deprecated`, say so in the answer.
