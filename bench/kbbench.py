#!/usr/bin/env python3
"""kbbench — retrieval benchmark for markdown knowledge bases.

Compares search engines on one or more KB repos against a gold QA set:
"which doc answers this question?" Each engine is a gitmark-compatible CLI
(`--root R index`, `--root R search Q -k K --json` → [{path, ...}]) or the
built-in `grep` baseline (what an agent does without a KB tool: rank files by
how many query terms they contain).

QA set = JSONL, one question per line:
    {"id": "x-01", "kind": "paraphrase|keyword|typo", "q": "...", "gold": ["docs/a.md"]}

Usage:
    kbbench.py --repo NAME=PATH --qa NAME=qa.jsonl [--repo ... --qa ...]
               --engine grep --engine v01=path/to/gitmark.py --engine new=skills/kb-search/gitmark.py
               [-k 10] [--json out.json]

Metrics per engine: hit@1, hit@5, MRR@k (by kind and overall), mean search
latency, index time, number of files the engine indexed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

WORD = re.compile(r"[\w\-]{3,}", re.UNICODE)
SKIP_DIRS = {".git", "node_modules", ".gitmark", ".venv", "venv", "dist", "build", "__pycache__"}


# ─────────────────────────── engines ───────────────────────────
class GrepEngine:
    """Baseline: an agent grepping the repo. Score = distinct query terms present
    in the file (case-insensitive), tie-break by total occurrences."""

    name = "grep"

    def index(self, root: Path) -> dict:
        t = time.perf_counter()
        self.docs = {}
        for p in sorted(root.rglob("*.md")):
            rel = p.relative_to(root)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            try:
                self.docs[rel.as_posix()] = p.read_text("utf-8", errors="replace").lower()
            except OSError:
                pass
        return {"files": len(self.docs), "index_s": time.perf_counter() - t}

    def search(self, root: Path, q: str, k: int) -> list:
        terms = {w.lower() for w in WORD.findall(q)}
        scored = []
        for rel, text in self.docs.items():
            hits = [text.count(t) for t in terms]
            distinct = sum(1 for h in hits if h)
            if distinct:
                scored.append((distinct, sum(hits), rel))
        scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
        return [r for _, _, r in scored[:k]]


class CliEngine:
    """Any gitmark-compatible CLI."""

    def __init__(self, name: str, script: Path, extra: list | None = None, env: dict | None = None):
        self.name, self.script, self.extra, self.env = name, script, extra or [], env

    def _run(self, root: Path, *args) -> str:
        r = subprocess.run([sys.executable, str(self.script), "--root", str(root), *args],
                           capture_output=True, text=True, timeout=600,
                           env={**os.environ, **self.env} if self.env else None)
        if r.returncode != 0:
            raise RuntimeError(f"{self.name}: {' '.join(args)} → {r.stderr.strip()[-400:]}")
        return r.stdout

    def index(self, root: Path) -> dict:
        db = root / ".gitmark" / "index.db"
        if db.exists():
            db.unlink()                      # engines have different schemas — always rebuild
        t = time.perf_counter()
        out = self._run(root, "index")
        m = re.search(r"(\d+)\s+(?:файл|files?)", out)
        return {"files": int(m.group(1)) if m else None, "index_s": time.perf_counter() - t}

    def search(self, root: Path, q: str, k: int) -> list:
        res = json.loads(self._run(root, "search", q, "-k", str(k), "--json", *self.extra) or "[]")
        seen, out = set(), []
        for r in res:                        # engines return chunks — collapse to files, keep order
            if r["path"] not in seen:
                seen.add(r["path"])
                out.append(r["path"])
        return out[:k]


# ─────────────────────────── scoring ───────────────────────────
def rank_of(found: list, gold: list) -> int | None:
    for i, p in enumerate(found, 1):
        if p in gold:
            return i
    return None


def summarize(rows: list, k: int) -> dict:
    n = len(rows) or 1
    ranks = [r["rank"] for r in rows]
    return {
        "n": len(rows),
        "hit@1": sum(1 for x in ranks if x == 1) / n,
        "hit@5": sum(1 for x in ranks if x and x <= 5) / n,
        f"mrr@{k}": sum(1 / x for x in ranks if x) / n,
        "lat_ms": 1000 * sum(r["lat"] for r in rows) / n,
    }


def run(repos: dict, qas: dict, engines: list, k: int) -> dict:
    results = {"k": k, "engines": {}}
    for eng in engines:
        per_q, per_repo = [], {}
        for name, root in repos.items():
            info = eng.index(root)
            per_repo[name] = info
            for line in Path(qas[name]).read_text("utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                t = time.perf_counter()
                try:
                    found = eng.search(root, item["q"], k)
                except Exception as e:      # an engine crash counts as a miss, but is reported
                    print(f"  ! {eng.name} {item['id']}: {e}", file=sys.stderr)
                    found = []
                lat = time.perf_counter() - t
                per_q.append({"repo": name, "id": item["id"], "kind": item.get("kind", "?"),
                              "q": item["q"], "gold": item["gold"], "found": found[:5],
                              "rank": rank_of(found, item["gold"]), "lat": lat})
        by = defaultdict(list)
        for r in per_q:
            by["ALL"].append(r)
            by["kind:" + r["kind"]].append(r)
            by["repo:" + r["repo"]].append(r)
        results["engines"][eng.name] = {
            "summary": {key: summarize(rows, k) for key, rows in sorted(by.items())},
            "repos": per_repo,
            "questions": per_q,
        }
    return results


def print_table(res: dict):
    k = res["k"]
    engines = list(res["engines"])
    keys = list(next(iter(res["engines"].values()))["summary"])
    metrics = ["hit@1", "hit@5", f"mrr@{k}"]
    w = max(len(x) for x in keys) + 2
    head = "".join(f"{e:>24}" for e in engines)
    print(f"\n{'slice':<{w}}{'n':>4}{head}")
    print(f"{'':<{w}}{'':>4}" + "".join(f"{'h@1  h@5  mrr':>24}" for _ in engines))
    for key in keys:
        n = res["engines"][engines[0]]["summary"][key]["n"]
        cells = ""
        for e in engines:
            s = res["engines"][e]["summary"][key]
            cells += f"{s['hit@1']:>14.2f}{s['hit@5']:>5.2f}{s[metrics[2]]:>5.2f}"
        print(f"{key:<{w}}{n:>4}{cells}")
    print(f"\n{'engine':<10}{'search ms':>11}{'index s / files per repo'}")
    for e in engines:
        r = res["engines"][e]
        idx = "  ".join(f"{n}:{v['index_s']:.1f}s/{v['files']}" for n, v in r["repos"].items())
        print(f"{e:<10}{r['summary']['ALL']['lat_ms']:>9.0f}  {idx}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", default=[], help="NAME=PATH")
    ap.add_argument("--qa", action="append", default=[], help="NAME=qa.jsonl")
    ap.add_argument("--engine", action="append", default=[],
                    help="'grep' or NAME=path/to/gitmark.py[,extra-search-args]")
    ap.add_argument("-k", type=int, default=10)
    ap.add_argument("--json", help="write full results (per question) here")
    a = ap.parse_args(argv)
    repos = {n: Path(p).resolve() for n, p in (x.split("=", 1) for x in a.repo)}
    qas = dict(x.split("=", 1) for x in a.qa)
    missing = set(repos) ^ set(qas)
    if missing:
        ap.error(f"--repo/--qa mismatch: {sorted(missing)}")
    engines = []
    for spec in a.engine or ["grep"]:
        if spec == "grep":
            engines.append(GrepEngine())
            continue
        name, _, rest = spec.partition("=")
        script, *extra = rest.split(",")
        engines.append(CliEngine(name, Path(script).resolve(), [x for x in extra if x]))
    res = run(repos, qas, engines, a.k)
    print_table(res)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
        print(f"\n→ {a.json}")


if __name__ == "__main__":
    main()
