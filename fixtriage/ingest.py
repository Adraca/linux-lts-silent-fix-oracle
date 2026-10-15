"""Walks a real git history and yields parsed commits. No blob/diff access
needed for the baseline (message + trailers only) -- keeps this usable even
against a partial/shallow clone.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .trailers import Trailers, parse as parse_trailers

_RECORD_SEP = "\x1e"
_FIELD_SEP = "\x1f"
_FORMAT = f"%H{_FIELD_SEP}%aI{_FIELD_SEP}%s{_FIELD_SEP}%b{_RECORD_SEP}"


@dataclass
class Commit:
    sha: str
    author_date: datetime
    subject: str
    body: str
    trailers: Trailers

    @property
    def message(self) -> str:
        return f"{self.subject}\n\n{self.body}"


class IngestError(RuntimeError):
    pass


def walk(
    repo: Path,
    since: str | None = None,
    until: str | None = None,
    ref: str = "HEAD",
    no_merges: bool = True,
) -> list[Commit]:
    if not (repo / ".git").exists():
        raise IngestError(f"{repo} doesn't look like a git checkout (no .git)")

    args = ["git", "-C", str(repo), "log", f"--format={_FORMAT}", ref]
    if no_merges:
        args.append("--no-merges")
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")

    try:
        out = subprocess.run(args, capture_output=True, text=True, check=True, timeout=120)
    except subprocess.CalledProcessError as e:
        raise IngestError(f"git log failed: {e.stderr}") from e
    except subprocess.TimeoutExpired as e:
        raise IngestError(f"git log timed out after 120s on {repo}") from e

    commits = []
    for record in out.stdout.split(_RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(_FIELD_SEP)
        if len(parts) != 4:
            continue  # malformed record (shouldn't happen with this format string)
        sha, date_str, subject, body = parts
        commits.append(
            Commit(
                sha=sha,
                author_date=datetime.fromisoformat(date_str),
                subject=subject,
                body=body,
                trailers=parse_trailers(f"{subject}\n\n{body}"),
            )
        )
    return commits


def upstream_shas_landed_in_stable(repo: Path, ref: str = "HEAD") -> set[str]:
    """The ground-truth set for evaluation: every mainline SHA that a real
    stable branch's own commit messages record as having backported (via the
    `commit <sha> upstream.` / `[ Upstream commit <sha> ]` convention)."""
    commits = walk(repo, ref=ref, no_merges=False)
    return {c.trailers.upstream_commit for c in commits if c.trailers.upstream_commit}
