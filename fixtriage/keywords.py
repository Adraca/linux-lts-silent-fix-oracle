"""The keyword+trailer baseline classifier. This baseline exists to
be measured, and be beaten before any model gets built -- so keep it boring,
keep it inspectable, and don't tune it against the evaluation set (that would
make the baseline artificially hard to beat and defeat the point).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .trailers import Trailers

# Bug-class vocabulary. Weighted by roughly how often each class corresponds
# to a real memory-safety/logic bug vs. a false-positive-prone generic word.
# Deliberately terse regexes on word boundaries -- avoid matching inside
# unrelated identifiers (e.g. "leak" inside "leaking_bucket_algorithm").
_KEYWORDS: dict[str, float] = {
    r"\buse.after.free\b": 3.0,
    r"\bdouble.free\b": 3.0,
    r"\bout.of.bounds?\b": 2.5,
    r"\boob\b": 1.5,
    r"\bbuffer overflow\b": 3.0,
    r"\bbuffer overrun\b": 2.5,
    r"\bheap overflow\b": 3.0,
    r"\bstack overflow\b": 2.0,
    r"\binteger overflow\b": 2.0,
    r"\bunderflow\b": 1.5,
    r"\bnull pointer\b": 1.5,
    r"\bnull.ptr.deref\b": 2.0,
    r"\bdangling pointer\b": 2.5,
    r"\brace condition\b": 2.0,
    r"\bdata race\b": 1.5,
    r"\bdeadlock\b": 1.0,
    r"\buninitiali[sz]ed\b": 1.5,
    r"\bmemory leak\b": 1.0,
    r"\binfo(?:rmation)? leak\b": 2.0,
    r"\bkasan\b": 1.5,
    r"\bkfence\b": 1.0,
    r"\bsyzbot\b": 1.0,
    r"\brefcount\b": 1.0,
    r"\buse.before.init\b": 1.5,
    r"\btype confusion\b": 2.5,
    r"\bprivilege escalation\b": 3.0,
    r"\bdenial of service\b": 1.0,
    r"\bsecurity\b": 1.0,
    r"\boverflow\b": 1.0,  # generic catch-all, low weight -- the specific
                            # variants above already scored the strong cases
}

_COMPILED = [(re.compile(pat, re.IGNORECASE), weight) for pat, weight in _KEYWORDS.items()]


@dataclass
class Score:
    keyword_score: float
    matched_keywords: list[str]
    trailer_score: float
    total: float


def score_message(message: str, trailers: Trailers) -> Score:
    matched = []
    keyword_score = 0.0
    for pattern, weight in _COMPILED:
        if pattern.search(message):
            keyword_score += weight
            matched.append(pattern.pattern)

    trailer_score = 0.0
    if trailers.reported_by_syzbot:
        trailer_score += 2.0  # syzkaller findings are disproportionately real bugs
    if trailers.reviewed_by_count >= 2:
        trailer_score += 0.5  # more eyes on a fix weakly correlates with it mattering

    return Score(
        keyword_score=round(keyword_score, 2),
        matched_keywords=matched,
        trailer_score=trailer_score,
        total=round(keyword_score + trailer_score, 2),
    )
