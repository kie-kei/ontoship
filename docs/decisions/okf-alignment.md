---
node_type: decision
title: Align with OKF frontmatter; measure search with a benchmark
description: "Why gitmark 0.2 adopted Open Knowledge Format fields (description, trust, stale_after), indexes frontmatter, and how the retrieval benchmark measured the gain over 0.1 and grep."
service: _platform
status: active
updated: 2026-10-15
tags: [okf, frontmatter, trust, benchmark, search, adr]
generated: { by: claude-code/opus-5-5, at: 2026-10-15T12:00:00Z }
links:
  documents: [../../skills/kb-search/gitmark.py, ../../bench/kbbench.py]
  depends_on: [../ontology.md]
  relates_to: [ontoship-positioning.md, ../reference/metrics.md]
---

# Decision: OKF-compatible frontmatter + a benchmark for search

## Context

Two outside signals in autumn 2026 pointed the same way: Google published the **Open
Knowledge Format** (a folder of markdown with YAML frontmatter, plus trust/provenance/
lifecycle fields), and a widely read post argued that plain text + frontmatter outlives
every vector/graph "company brain" — frontmatter turns a folder into something an agent
can *query* (who attended, what is verified, by whom) without a database.

Running gitmark 0.1 over seven real project KBs showed it did not live up to its own model:

- **Typed links were never parsed.** The frontmatter parser ignored indentation, so
  `links:` was always `{}` across ~300 docs that declare it; I3/I6 could not work and the
  graph had no link types.
- `lint` **crashed** on list-valued `service:` and kept YAML comments inside values.
- Discovery walked the filesystem: 5 271 vendored md files indexed in one repo (25 s),
  a docs copy used as test data outranked the real docs in another.
- Frontmatter was not indexed at all — no title/description boost, no type/status filter,
  deprecated docs ranked like live ones.

## Decision

1. **Read OKF frontmatter natively**: `type` = `node_type`, `description`, `generated` /
   `verified` (derived trust tier), `stale_after`, `status: stable`, root-relative links.
   Keep OntoShip's additions (typed links, controlled vocabularies, lint).
2. **Real YAML**: PyYAML when present, a stdlib subset parser otherwise (same output on
   our fixtures, tolerant of `title: a: b`).
3. **Index frontmatter** and rank per file: chunk bm25 + doc-level bm25 over
   title/description/tags/path + trigram phrase + fuzzy, fused with RRF; priors for
   typed docs, penalties for indexes/changelogs, deprecated and stale docs.
4. **Discover via git** (`ls-files -co --exclude-standard`) + `.gitmarkignore`.
5. **`gitmark query`** for structured questions over frontmatter, read straight from md.
6. **Measure, don't argue**: `bench/kbbench.py` — gold QA sets per repo, hit@1/hit@5/MRR.

## Results (198 questions, 7 real repos; QA sets private, harness in `bench/`)

| engine | hit@1 | hit@5 | MRR@10 |
|---|---|---|---|
| grep (agent without the skill) | 0.30 | 0.67 | 0.46 |
| gitmark 0.1 | 0.47 | 0.82 | 0.62 |
| **gitmark 0.2** | **0.69** | **0.93** | **0.80** |

By query kind (0.1 → 0.2, hit@1): paraphrase 0.43 → 0.64, keyword 0.60 → 0.80,
typo 0.47 → 0.75. Index time on the vendored repo: 25 s → 0.5 s.

**`description` experiment** (3 repos, 90 questions; descriptions added by an agent to a
mirror, nothing else changed):

| engine | hit@1 without → with | MRR without → with |
|---|---|---|
| grep | 0.29 → 0.41 | 0.47 → 0.56 |
| gitmark 0.1 | 0.47 → 0.57 | 0.65 → 0.71 |
| gitmark 0.2 | 0.77 → 0.83 | 0.85 → 0.89 |

The one-line summary helps *every* consumer, including plain grep — structure in plain
text pays off without any tooling. Hence `description` is now recommended for every
load-bearing doc (`kb-curate`).

Ranking weights were tuned on a dev split (odd questions) and checked on the held-out
even half; the tuned config moved test MRR 0.753 → 0.795, and the top dev configs were
within noise of each other. Most of the gain is structural (discovery, per-file fusion,
frontmatter fields), not weight-fiddling.

## Caveats

- QA sets and descriptions were written by an LLM from the docs themselves; absolute
  numbers are optimistic. Relative comparisons on the same set are the point.
- Search is still lexical. Paraphrases with no shared vocabulary remain the ceiling
  (hit@5 0.89); the skill tells the agent to reformulate (ru↔en, identifiers, synonyms).
- Not yet measured: end-to-end agent answers (with vs without the skill, tokens/turns).

## Consequences

- KB docs should carry `description`; agent-written docs carry `generated`; only real
  verifiers add `verified`.
- Every change to ranking must come with a `bench/` run; regressions are visible per repo
  and per query kind.
