"""Real-data integration tests, gated on real mainline+stable checkouts per
the real-fixture testing methodology. Never vendored into this repo (they're
multi-hundred-MB git histories) -- point KERNEL_MAINLINE/KERNEL_STABLE at
real clones (see README.md) to run this.
"""

import os
from pathlib import Path

import pytest

from fixtriage import ingest
from fixtriage.classify import find_candidates
from fixtriage.evaluate import evaluate

MAINLINE = os.environ.get("KERNEL_MAINLINE") or os.environ.get("FIXTRIAGE_KERNEL_REPO")
STABLE = os.environ.get("KERNEL_STABLE") or os.environ.get("FIXTRIAGE_KERNEL_REPO")

pytestmark = pytest.mark.skipif(
    not (MAINLINE and STABLE),
    reason="KERNEL_MAINLINE/KERNEL_STABLE or FIXTRIAGE_KERNEL_REPO not set (see tests/README.md)",
)


def test_ingest_real_mainline_window():
    commits = ingest.walk(Path(MAINLINE), since="2023-06-01", until="2024-06-01")
    assert len(commits) > 1000, "a year of real mainline history should be well over 1000 commits"
    # Spot-check: every commit has a real 40-char sha and a non-empty subject.
    for c in commits[:50]:
        assert len(c.sha) == 40
        assert c.subject.strip()


def test_candidates_are_a_real_subset_with_fixes_and_no_cc_stable():
    commits = ingest.walk(Path(MAINLINE), since="2023-06-01", until="2023-09-01")
    candidates = find_candidates(commits)
    assert 0 < len(candidates) < len(commits)
    for c in candidates:
        assert c.fixes_sha
    # Cross-check against the raw commits: no candidate should have had
    # Cc:stable (that's the whole point of "silent").
    by_sha = {c.sha: c for c in commits}
    for cand in candidates:
        assert not by_sha[cand.sha].trailers.cc_stable


def test_ground_truth_extraction_finds_real_backports():
    landed = ingest.upstream_shas_landed_in_stable(Path(STABLE))
    assert len(landed) > 100, "a real long-term-stable branch should have hundreds of tracked backports"
    for sha in list(landed)[:20]:
        assert len(sha) == 40


def test_evaluate_end_to_end_on_a_window_old_enough_to_have_backports():
    # Old enough (per README's own caution) that backporting has had real
    # time to happen -- not last week's commits.
    commits = ingest.walk(Path(MAINLINE), since="2023-06-01", until="2023-12-01")
    candidates = find_candidates(commits)
    landed = ingest.upstream_shas_landed_in_stable(Path(STABLE))
    report = evaluate(candidates, landed)

    assert report.total_candidates == len(candidates)
    assert report.ground_truth_positive >= 0
    assert report.trivial_flag_everything_recall == 1.0
    # Monotonicity sanity check: recall must never increase as the threshold
    # rises (a stricter cutoff can only flag a subset of what a looser one
    # flagged) -- a violation here would mean a real logic bug in evaluate().
    prev_recall = None
    for r in sorted(report.thresholds, key=lambda x: x.threshold):
        if prev_recall is not None:
            assert r.recall <= prev_recall + 1e-9
        prev_recall = r.recall
