"""Fetch and analyze kernel commits from git repositories.

This module handles:
1. Cloning/fetching mainline and LTS kernel repos
2. Extracting commit metadata
3. Identifying patches in mainline but not in LTS
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from fixtriage.gap_analyzer import PatchGap


class KernelGitAnalyzer:
    """Analyze kernel git repositories for patch gaps."""

    # Known git URLs for kernel repos
    MAINLINE_URL = "https://github.com/torvalds/linux.git"
    STABLE_URL = "https://github.com/gregkh/linux-stable.git"

    LTS_BRANCHES = {
        "5.15": "linux-5.15.y",
        "6.1": "linux-6.1.y",
        "6.6": "linux-6.6.y",
    }

    def __init__(self, repo_path: Path = None):
        """Initialize analyzer.

        Args:
            repo_path: Path to local kernel git repo (will use mainline or stable)
        """
        self.repo_path = repo_path or Path.home() / "linux-kernel"

    def run_git(self, *args, repo_path: Path | None = None) -> str:
        """Run git command in repo.

        Args:
            *args: git command arguments
            repo_path: Optional specific repo path

        Returns:
            git command output
        """
        path = repo_path or self.repo_path
        cmd = ["git", "-C", str(path)] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()

    def get_commits(self, branch: str = "master", limit: int = 100) -> list[str]:
        """Get commit hashes from a branch.

        Args:
            branch: Branch name (e.g., 'master', 'linux-6.1.y')
            limit: Maximum commits to fetch

        Returns:
            List of commit hashes
        """
        try:
            output = self.run_git("log", f"--oneline", f"--max-count={limit}", branch)
            commits = []
            for line in output.split("\n"):
                if line.strip():
                    # Format: "abc123def commit message"
                    hash_part = line.split()[0]
                    commits.append(hash_part)
            return commits
        except Exception as e:
            print(f"Error fetching commits from {branch}: {e}")
            return []

    def get_commit_details(self, commit_hash: str, repo_path: Path | None = None) -> dict:
        """Get detailed metadata for a commit.

        Args:
            commit_hash: Commit SHA or partial SHA
            repo_path: Optional specific repo path

        Returns:
            Dict with: hash, subject, author, date, files
        """
        try:
            # Get commit info
            output = self.run_git(
                "show", "-s", "--format=%H|%s|%an|%ai|%b", commit_hash, repo_path=repo_path
            )

            if not output:
                return {}

            parts = output.split("|", 4)
            if len(parts) < 4:
                return {}

            # Get affected files
            files_output = self.run_git("show", "--name-only", "--pretty=", commit_hash, repo_path=repo_path)
            files = [f for f in files_output.split("\n") if f.strip()]

            return {
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3],
                "message": parts[4] if len(parts) > 4 else "",
                "files": files,
            }
        except Exception as e:
            print(f"Error fetching details for {commit_hash}: {e}")
            return {}

    def check_commit_in_branch(self, commit_hash: str, branch: str, repo_path: Path | None = None) -> bool:
        """Check if a commit exists in a specific branch.

        Args:
            commit_hash: Commit SHA
            branch: Branch name
            repo_path: Optional specific repo path

        Returns:
            True if commit is in branch, False otherwise
        """
        try:
            output = self.run_git(
                "log", "--oneline", branch, f"--grep={commit_hash}", repo_path=repo_path
            )
            # Also check by direct merge-base
            result = subprocess.run(
                ["git", "-C", str(repo_path or self.repo_path), "merge-base", "--is-ancestor", commit_hash, branch],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def find_gaps(self, mainline_commits: list[str], max_gaps: int = 100) -> list[PatchGap]:
        """Identify commits in mainline but not in LTS branches.

        Args:
            mainline_commits: List of commits from mainline
            max_gaps: Maximum gaps to return

        Returns:
            List of PatchGap objects
        """
        gaps = []

        for commit_hash in mainline_commits[:max_gaps * 2]:  # Check more than needed
            details = self.get_commit_details(commit_hash)
            if not details:
                continue

            # Check presence in each LTS branch
            in_515 = self.check_commit_in_branch(commit_hash, self.LTS_BRANCHES["5.15"])
            in_61 = self.check_commit_in_branch(commit_hash, self.LTS_BRANCHES["6.1"])
            in_66 = self.check_commit_in_branch(commit_hash, self.LTS_BRANCHES["6.6"])

            # Only include if missing from at least one LTS branch
            if not (in_515 and in_61 and in_66):
                # Parse date
                try:
                    date = datetime.fromisoformat(details["date"].replace(" +", "+"))
                except Exception:
                    date = datetime.now()

                # Get primary affected file
                affected_file = details["files"][0] if details["files"] else "unknown"

                gap = PatchGap(
                    commit_hash=commit_hash,
                    commit_msg=details["subject"] + "\n" + details["message"],
                    author=details["author"],
                    date=date,
                    affected_file=affected_file,
                    in_mainline=True,
                    in_lts_515=in_515,
                    in_lts_61=in_61,
                    in_lts_66=in_66,
                )

                gaps.append(gap)

                if len(gaps) >= max_gaps:
                    break

        return gaps


def analyze_kernel_repos(mainline_path: Path | None = None, stable_path: Path | None = None) -> list[PatchGap]:
    """Analyze mainline and LTS kernel repos for patch gaps (high-level API).

    Args:
        mainline_path: Path to mainline kernel repo
        stable_path: Path to stable kernel repo

    Returns:
        List of identified patch gaps
    """
    analyzer = KernelGitAnalyzer(mainline_path)

    print("Fetching commits from mainline...")
    mainline_commits = analyzer.get_commits("master", limit=200)
    print(f"  Found {len(mainline_commits)} recent commits")

    print("Identifying patch gaps...")
    gaps = analyzer.find_gaps(mainline_commits, max_gaps=50)
    print(f"  Identified {len(gaps)} patch gaps")

    return gaps
