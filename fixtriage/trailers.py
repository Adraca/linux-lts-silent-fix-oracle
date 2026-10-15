"""Parses the trailers/markers this whole pipeline depends on, out of a raw
commit message. Real Linux commit conventions, not invented ones -- verified
against actual `git log` output on the real mainline/stable clones this tool
runs against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# `Fixes: <12-or-40-hex-sha> ("subject of the commit being fixed")`
_FIXES_RE = re.compile(r"^Fixes:\s*([0-9a-f]{8,40})\b", re.MULTILINE | re.IGNORECASE)

# `Cc: stable@vger.kernel.org` -- with or without angle brackets, with or
# without a version qualifier like `# 6.1+` some maintainers append.
_CC_STABLE_RE = re.compile(r"^Cc:\s*<?stable@vger\.kernel\.org>?", re.MULTILINE | re.IGNORECASE)

# `Reported-by: syzbot+<hash>@syzkaller.appspotmail.com`
_SYZBOT_RE = re.compile(r"^Reported-by:.*syzkaller\.appspotmail\.com", re.MULTILINE | re.IGNORECASE)

_REVIEWED_BY_RE = re.compile(r"^Reviewed-by:", re.MULTILINE | re.IGNORECASE)

# The two real conventions stable trees use to record which mainline commit a
# backport came from. Both appear in real `git log` output on stable branches.
_UPSTREAM_COMMIT_RE = re.compile(
    r"(?:^|\n)\s*(?:\[\s*)?commit\s+([0-9a-f]{40})\s+upstream\.?", re.IGNORECASE
)
_UPSTREAM_BRACKET_RE = re.compile(
    r"\[\s*Upstream commit\s+([0-9a-f]{40})\s*\]", re.IGNORECASE
)


@dataclass
class Trailers:
    fixes_sha: str | None = None
    cc_stable: bool = False
    reported_by_syzbot: bool = False
    reviewed_by_count: int = 0
    upstream_commit: str | None = None  # only set on stable-tree commits


def parse(message: str) -> Trailers:
    fixes_match = _FIXES_RE.search(message)
    upstream_match = _UPSTREAM_COMMIT_RE.search(message) or _UPSTREAM_BRACKET_RE.search(message)
    return Trailers(
        fixes_sha=fixes_match.group(1) if fixes_match else None,
        cc_stable=bool(_CC_STABLE_RE.search(message)),
        reported_by_syzbot=bool(_SYZBOT_RE.search(message)),
        reviewed_by_count=len(_REVIEWED_BY_RE.findall(message)),
        upstream_commit=upstream_match.group(1) if upstream_match else None,
    )
