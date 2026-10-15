"""Trailer parsing against a real commit message (not synthetic) -- see
fixtures/real_stable_backport.txt for provenance (a real linux-6.1.y commit,
fetched directly from kernel.org during this tool's own build)."""

from pathlib import Path

from fixtriage.trailers import parse

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_real_backport_commit_parses_correctly():
    msg = _load("real_stable_backport.txt")
    t = parse(msg)
    assert t.fixes_sha == "6fe26f694c82"
    assert t.cc_stable is True
    assert t.reported_by_syzbot is False
    assert t.reviewed_by_count == 0
    assert t.upstream_commit == "8f2f62855a41d1730fb9e8122912bd2c8d6bed5d"


def test_no_trailers_present():
    t = parse("net: fix typo in a comment\n\nNo functional change.\n")
    assert t.fixes_sha is None
    assert t.cc_stable is False
    assert t.upstream_commit is None


def test_cc_stable_variants():
    assert parse("Fixes: abc12345 (\"x\")\nCc: stable@vger.kernel.org\n").cc_stable
    assert parse("Fixes: abc12345 (\"x\")\nCc: <stable@vger.kernel.org>\n").cc_stable
    assert parse("Fixes: abc12345 (\"x\")\nCc: someone@example.com\n").cc_stable is False


def test_syzbot_report_detected():
    msg = (
        "net: fix null deref\n\n"
        "Reported-by: syzbot+abcdef1234567890@syzkaller.appspotmail.com\n"
    )
    assert parse(msg).reported_by_syzbot is True


def test_reviewed_by_counts_multiple():
    msg = (
        "x\n\n"
        "Reviewed-by: A <a@example.com>\n"
        "Reviewed-by: B <b@example.com>\n"
    )
    assert parse(msg).reviewed_by_count == 2
