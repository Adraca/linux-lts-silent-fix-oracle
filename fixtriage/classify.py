"""Turns ingested commits into ranked silent-fix candidates. By definition:
candidate = has Fixes:, doesn't have Cc:stable. Ranking = the keyword+trailer
baseline score, nothing fancier yet.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .ingest import Commit
from .keywords import Score, score_message


@dataclass
class Candidate:
    sha: str
    author_date: str
    subject: str
    fixes_sha: str
    score: Score
    matched_keywords: list[str]


def find_candidates(commits: list[Commit]) -> list[Candidate]:
    """A commit is a candidate iff it names what it fixes but was never
    flagged for backport -- the mechanical definition used here. This is
    NOT itself the security judgment; the keyword score below is."""
    candidates = []
    for c in commits:
        if c.trailers.fixes_sha is None or c.trailers.cc_stable:
            continue
        s = score_message(c.message, c.trailers)
        candidates.append(
            Candidate(
                sha=c.sha,
                author_date=c.author_date.isoformat(),
                subject=c.subject,
                fixes_sha=c.trailers.fixes_sha,
                score=s,
                matched_keywords=s.matched_keywords,
            )
        )
    candidates.sort(key=lambda c: c.score.total, reverse=True)
    return candidates


def candidate_to_dict(c: Candidate) -> dict:
    d = asdict(c)
    return d
