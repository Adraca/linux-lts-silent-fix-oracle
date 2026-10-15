"""Analyze patch gaps between mainline and LTS kernel branches."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PatchGap:
    """A security fix in mainline that's missing from LTS branches."""

    commit_hash: str  # Short or full git hash
    commit_msg: str
    author: str
    date: datetime
    affected_file: str

    # Presence in kernel branches
    in_mainline: bool = True
    in_lts_515: bool = False
    in_lts_61: bool = False
    in_lts_66: bool = False

    # Scoring
    exploitability_score: float = 0.0
    keywords: list[str] = field(default_factory=list)
    cve_id: str | None = None

    @property
    def days_in_mainline(self) -> int:
        """Estimate days since merged to mainline."""
        # Placeholder - would be set based on actual date
        return 0

    @property
    def unpatched_branches(self) -> list[str]:
        """List of LTS branches that still have this vuln."""
        unpatched = []
        if not self.in_lts_515:
            unpatched.append("5.15")
        if not self.in_lts_61:
            unpatched.append("6.1")
        if not self.in_lts_66:
            unpatched.append("6.6")
        return unpatched


class ExploitabilityScorer:
    """Score patch gaps by exploitability."""

    # Keyword → base score
    VULN_KEYWORDS = {
        "use-after-free": 40,
        "uaf": 40,
        "use after free": 40,
        "double-free": 38,
        "double free": 38,
        "heap overflow": 35,
        "buffer overflow": 33,
        "stack overflow": 32,
        "out of bounds": 28,
        "oob": 28,
        "race condition": 25,
        "race": 25,
        "information disclosure": 20,
        "privilege escalation": 45,
        "arbitrary write": 42,
        "arbitrary read": 20,
        "type confusion": 22,
        "integer overflow": 24,
        "null pointer": 15,
        "deadlock": 10,
    }

    # Subsystem → importance multiplier
    SUBSYSTEM_IMPORTANCE = {
        "mm/": 1.8,  # Memory management - critical
        "fs/": 1.7,  # Filesystem - common attack surface
        "kernel/": 1.6,  # Core kernel
        "net/core/": 1.5,  # Networking core
        "arch/": 1.6,  # Architecture-specific
        "drivers/": 0.8,  # Device drivers - less critical
        "sound/": 0.3,  # Audio - very low
        "tools/": 0.2,  # Tools - minimal
    }

    @classmethod
    def score(cls, gap: PatchGap) -> float:
        """Compute exploitability score for a patch gap.

        Scoring formula:
        - Base: keyword score (0-45)
        - File subsystem: x0.3 to x1.8
        - CVE presence: +25
        - Days unpatched: +0.5 per week

        Returns:
            Score (0-100+)
        """
        score = 0.0

        # Extract keywords
        text = (gap.commit_msg + " " + gap.affected_file).lower()
        found_keywords = []

        for keyword, base_score in cls.VULN_KEYWORDS.items():
            if keyword in text:
                score += base_score
                found_keywords.append(keyword)

        # Subsystem multiplier
        subsystem_mult = 1.0
        for prefix, mult in cls.SUBSYSTEM_IMPORTANCE.items():
            if gap.affected_file.startswith(prefix):
                subsystem_mult = mult
                break

        score *= subsystem_mult

        # CVE bonus
        if gap.cve_id:
            score += 25

        # Time penalty: more days unpatched = higher score
        days_unpatched = gap.days_in_mainline
        if days_unpatched > 7:
            score += (days_unpatched // 7) * 0.5

        # Security-related keywords add extra
        security_keywords = ["security", "fix", "patch", "cve"]
        if any(kw in text for kw in security_keywords):
            score += 5

        return min(score, 100.0)  # Cap at 100

    @classmethod
    def extract_keywords(cls, text: str) -> list[str]:
        """Extract vulnerability keywords from text."""
        keywords = []
        text_lower = text.lower()

        for keyword in cls.VULN_KEYWORDS.keys():
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords

    @classmethod
    def extract_cve(cls, text: str) -> str | None:
        """Extract CVE ID from text."""
        match = re.search(r"CVE-\d{4}-\d{4,}", text, re.IGNORECASE)
        return match.group(0) if match else None


def score_gap(gap: PatchGap) -> PatchGap:
    """Add exploitability score to a patch gap."""
    scorer = ExploitabilityScorer()
    score = scorer.score(gap)
    keywords = scorer.extract_keywords(gap.commit_msg)
    cve = scorer.extract_cve(gap.commit_msg)

    # Return new gap with scores
    return PatchGap(
        commit_hash=gap.commit_hash,
        commit_msg=gap.commit_msg,
        author=gap.author,
        date=gap.date,
        affected_file=gap.affected_file,
        in_mainline=gap.in_mainline,
        in_lts_515=gap.in_lts_515,
        in_lts_61=gap.in_lts_61,
        in_lts_66=gap.in_lts_66,
        exploitability_score=score,
        keywords=keywords,
        cve_id=cve,
    )


def rank_gaps(gaps: list[PatchGap]) -> list[tuple[PatchGap, float]]:
    """Rank patch gaps by exploitability score.

    Args:
        gaps: List of PatchGap objects

    Returns:
        List of (gap, score) tuples sorted by score descending
    """
    scored_gaps = []

    for gap in gaps:
        scored_gap = score_gap(gap)
        scored_gaps.append((scored_gap, scored_gap.exploitability_score))

    # Sort by score descending
    return sorted(scored_gaps, key=lambda x: x[1], reverse=True)
