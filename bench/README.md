# kbbench — retrieval benchmark for markdown KBs

Answers one question with numbers: **given a question, does the engine put the doc that
answers it at the top?** Used to compare gitmark versions against each other and against
`grep` (what an agent does without the skill).

## QA set

JSONL, one question per line, `gold` = repo-relative path(s) of the answering doc:

```json
{"id": "acme-01", "kind": "paraphrase", "q": "how do we roll back a bad deploy?", "gold": ["docs/ops/deploy.md"]}
```

`kind`: `paraphrase` (natural question, not copying the title), `keyword` (2–4 terms you
would type), `typo` (keywords with realistic typos / wrong morphology). Generate ~30 per
repo — an agent reading 30 docs and writing one question each works well; ask it to
describe the need the way someone who has *not* read the doc would.

QA sets describe private projects, so keep them out of git: `bench/local/` and
`bench/results/` are gitignored.

## Run

```bash
python3 bench/kbbench.py \
  --repo acme=~/src/acme --qa acme=bench/local/acme.jsonl \
  --repo beta=~/src/beta --qa beta=bench/local/beta.jsonl \
  --engine grep \
  --engine old=bench/local/variants/gitmark_v01.py \
  --engine new=skills/kb-search/gitmark.py \
  --json bench/results/run.json
```

`--engine NAME=path/to/gitmark.py[,extra,search,args]` — any gitmark-compatible CLI
(`--root R index`, `--root R search Q -k K --json`). The previous version is one
`git show <ref>:skills/kb-search/gitmark.py > …` away.

Engines rebuild `.gitmark/index.db` inside each repo. To leave real repos untouched, run
against a mirror: copy just the `*.md` (+ `.gitignore`, `.gitmarkignore`) into a scratch
dir, `git init` it and `git add` the files the original repo tracks.

Output: hit@1, hit@5, MRR@k overall, per query kind and per repo; search latency; index
time and file count per repo. `--json` keeps per-question ranks and top-5 for failure
analysis.

## Tuning

`gitmark.py` reads `GITMARK_TUNE='{"CHANNEL_W": {...}, "PRIOR": {...}, "RRF_K": 5}'` so
ranking weights can be grid-searched without editing code. Split questions into dev/test
(e.g. odd/even), pick on dev, report test.

## Results so far

See [docs/decisions/okf-alignment.md](../docs/decisions/okf-alignment.md).
