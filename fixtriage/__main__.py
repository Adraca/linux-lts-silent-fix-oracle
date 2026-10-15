"""CLI entry point.

    python -m fixtriage candidates --repo /path/to/mainline --since 2023-06-01 --json
    python -m fixtriage evaluate --repo /path/to/mainline --stable-repo /path/to/stable-6.1.y --since 2023-06-01 --until 2025-01-01 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import ingest
from .classify import candidate_to_dict, find_candidates
from .evaluate import evaluate


def _readable_keyword(pattern: str) -> str:
    """Strip regex furniture (\\b word boundaries, escaped dots) for display."""
    return pattern.replace(r"\b", "").replace(r"\.", " ").replace(r"?", "").strip()


def _cmd_candidates(args) -> int:
    commits = ingest.walk(args.repo, since=args.since, until=args.until, ref=args.ref)
    all_candidates = find_candidates(commits)
    candidates = all_candidates[: args.top] if args.top else all_candidates

    if args.json:
        print(json.dumps([candidate_to_dict(c) for c in candidates], indent=2))
    else:
        print(f"{len(commits)} commits scanned, {len(all_candidates)} silent-fix candidates\n")
        for c in candidates:
            print(f"{c.score.total:>5.1f}  {c.sha[:12]}  {c.author_date[:10]}  {c.subject}")
            if c.matched_keywords:
                readable = ", ".join(_readable_keyword(k) for k in c.matched_keywords)
                print(f"       matched: {readable}")
    return 0


def _cmd_evaluate(args) -> int:
    commits = ingest.walk(args.repo, since=args.since, until=args.until, ref=args.ref)
    candidates = find_candidates(commits)
    landed = ingest.upstream_shas_landed_in_stable(args.stable_repo, ref=args.stable_ref)
    report = evaluate(candidates, landed)

    if args.json:
        d = asdict(report)
        print(json.dumps(d, indent=2))
    else:
        print(f"candidates: {report.total_candidates}")
        print(f"ground-truth positives (later landed in stable anyway): {report.ground_truth_positive}")
        print(f"real class imbalance: {report.class_imbalance}")
        print(
            f"trivial 'flag everything' baseline: "
            f"precision={report.trivial_flag_everything_precision} recall=1.0"
        )
        print()
        print(f"{'threshold':>10} {'flagged':>8} {'TP':>5} {'FP':>5} {'precision':>10} {'recall':>7}")
        for r in report.thresholds:
            p = f"{r.precision:.4f}" if r.precision is not None else "n/a"
            print(f"{r.threshold:>10.1f} {r.predicted_positive:>8} {r.true_positive:>5} {r.false_positive:>5} {p:>10} {r.recall:>7.4f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fixtriage", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    common = dict(type=Path)
    p_cand = sub.add_parser("candidates", help="list ranked silent-fix candidates")
    p_cand.add_argument("--repo", required=True, **common)
    p_cand.add_argument("--since")
    p_cand.add_argument("--until")
    p_cand.add_argument("--ref", default="HEAD")
    p_cand.add_argument("--top", type=int, default=0)
    p_cand.add_argument("--json", action="store_true")
    p_cand.set_defaults(func=_cmd_candidates)

    p_eval = sub.add_parser("evaluate", help="measure baseline precision/recall against real backport history")
    p_eval.add_argument("--repo", required=True, **common)
    p_eval.add_argument("--stable-repo", required=True, **common)
    p_eval.add_argument("--since")
    p_eval.add_argument("--until")
    p_eval.add_argument("--ref", default="HEAD")
    p_eval.add_argument("--stable-ref", default="HEAD")
    p_eval.add_argument("--json", action="store_true")
    p_eval.set_defaults(func=_cmd_evaluate)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except ingest.IngestError as e:
        print(f"fixtriage: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
