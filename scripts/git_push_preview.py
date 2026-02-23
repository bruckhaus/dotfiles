#!/usr/bin/env python3
"""Rich git push preview helper."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List


LABEL = "\033[1;36m"
VALUE = "\033[0;33m"
COMMIT = "\033[0;32m"
DIM = "\033[2m"
RESET = "\033[0m"


def run_git(args: List[str]) -> str:
    """Run a git command and return stdout (stripped)."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        if not message:
            message = f"git {' '.join(args)} failed with exit code {result.returncode}"
        raise RuntimeError(message)
    return result.stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize what 'git push' would send to the upstream tracking branch."
    )
    parser.add_argument(
        "-f",
        "--full-file-list",
        action="store_true",
        help="Show every changed file instead of truncating to the first five entries.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Number of files to show before truncating (default: %(default)s).",
    )
    return parser


def print_header(upstream: str, ahead_behind: str, commit_count: str) -> None:
    print(
        f"{LABEL}Upstream{RESET}{DIM} (where you will push to){RESET}: {VALUE}{upstream}{RESET}"
    )
    print(
        f"{LABEL}Behind/Ahead{RESET}{DIM} (left=behind, right=ahead){RESET}: "
        f"{VALUE}{ahead_behind}{RESET}"
    )
    print(
        f"{LABEL}Commits to push{RESET}: {VALUE}{commit_count}{RESET}"
    )
    print(
        f"{LABEL}Commit list{RESET}{DIM} (new commits on your branch){RESET}:"
    )


def format_commit_line(line: str) -> str:
    import re

    match = re.match(r"^(\S+)(?:\s+\((.*?)\))?\s+(.*)$", line)
    if not match:
        return line

    commit_hash, refs, message = match.groups()
    parts = [commit_hash]
    if refs:
        parts.append(f" ({refs})")
    if message:
        parts.append(f" {COMMIT}{message}{RESET}")
    return "".join(parts)


def print_commit_list(commits: str) -> None:
    if commits:
        for line in commits.splitlines():
            print(format_commit_line(line))
    else:
        print(f"{DIM}(none){RESET}")


def print_file_changes(files: List[str], show_full: bool, max_files: int) -> None:
    print(
        f"{LABEL}Files changed{RESET}{DIM} (what will change on remote after push){RESET}:"
    )

    if not files:
        print(f"{DIM}(none){RESET}")
        return

    if show_full or len(files) <= max_files:
        for entry in files:
            print(entry)
        return

    for entry in files[:max_files]:
        print(entry)

    remaining = len(files) - max_files
    print(
        f"{DIM}Total {len(files)} files ({remaining} more). "
        f"Run 'gpp --full-file-list' to show all.{RESET}"
    )


def has_upstream() -> bool:
    """Check if the current branch has an upstream tracking branch."""
    try:
        run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        return True
    except RuntimeError:
        return False


def gather_push_preview(show_full: bool, max_files: int) -> None:
    if has_upstream():
        upstream = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        ahead_behind = run_git(["rev-list", "--left-right", "--count", "@{u}...HEAD"])
        commit_count = run_git(["rev-list", "--count", "@{u}..HEAD"])
        commit_list = run_git(["log", "--oneline", "--decorate", "@{u}..HEAD"])
        files_raw = run_git(["diff", "--name-status", "@{u}..HEAD"])
    else:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        upstream = f"(no upstream; showing all commits on {branch})"
        commit_count = run_git(["rev-list", "--count", "HEAD"])
        ahead_behind = f"0\t{commit_count}"
        commit_list = run_git(["log", "--oneline", "--decorate"])
        # Show files changed across all commits
        root_tree = run_git(["hash-object", "-t", "tree", "/dev/null"])
        files_raw = run_git(["diff", "--name-status", root_tree, "HEAD"])

    files_changed = [line for line in files_raw.splitlines() if line.strip()]

    print_header(upstream, ahead_behind, commit_count)
    print_commit_list(commit_list)
    print_file_changes(files_changed, show_full, max_files)


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        gather_push_preview(args.full_file_list, args.max_files)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("This command must be run inside a git repository.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
