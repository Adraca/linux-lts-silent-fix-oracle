"""Baseline scorer tests -- the real fixture (a genuine use-after-free fix)
should score meaningfully positive; unrelated text should score zero."""

from pathlib import Path

from fixtriage.keywords import score_message
from fixtriage.trailers import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_real_uaf_commit_scores_positive():
    msg = (FIXTURES / "real_stable_backport.txt").read_text()
    t = parse(msg)
    s = score_message(msg, t)
    assert s.total > 0
    assert any("use.after.free" in k for k in s.matched_keywords)


def test_unrelated_commit_scores_zero():
    msg = "docs: fix a typo in the networking guide\n\nNo functional change.\n"
    t = parse(msg)
    s = score_message(msg, t)
    assert s.total == 0
    assert s.matched_keywords == []


def test_syzbot_trailer_adds_to_score_even_without_keyword_match():
    msg_plain = "some: fix an edge case\n\nDetails.\n"
    msg_syzbot = msg_plain + "Reported-by: syzbot+deadbeef@syzkaller.appspotmail.com\n"
    t_plain = parse(msg_plain)
    t_syzbot = parse(msg_syzbot)
    assert score_message(msg_syzbot, t_syzbot).total > score_message(msg_plain, t_plain).total


def test_specific_keyword_beats_generic_overflow_catchall():
    # "heap overflow" should score higher than the bare generic "overflow"
    # catch-all alone -- specificity is weighted, per keywords.py's design.
    t = parse("x")
    specific = score_message("fix heap overflow in foo", t)
    generic = score_message("fix overflow in foo", t)
    assert specific.total > generic.total
