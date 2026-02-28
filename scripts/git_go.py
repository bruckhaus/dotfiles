#!/usr/bin/env python3
"""Interactive helper for jumping between git repositories under one or more roots."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Dict, Iterable, List, Sequence, TypedDict


DEFAULT_CACHE_PATH = os.path.expanduser(
    os.environ.get("GIT_GO_CACHE", "~/.cache/git_go/repos.json")
)
DEFAULT_CACHE_TTL = int(
    os.environ.get("GIT_GO_CACHE_TTL", str(7 * 24 * 60 * 60))
)


class CacheEntry(TypedDict, total=False):
    timestamp: float
    repos: List[str]
    ttl: int


CacheData = Dict[str, CacheEntry]


def find_git_repos(root: str) -> List[str]:
    repos: List[str] = []
    for current_path, dirnames, _ in os.walk(root):
        if ".git" in dirnames:
            repos.append(current_path)

        # Skip undesired directories but still allow traversal into nested repos.
        dirnames[:] = [
            d for d in dirnames
            if d not in {".git", ".venv", "venv", "__pycache__"}
        ]
    repos.sort()
    return repos


def format_repo(path: str, root: str) -> str:
    try:
        rel = os.path.relpath(path, root)
        if not rel.startswith(".."):
            return rel
    except ValueError:
        pass
    return path


def filter_repos(repos: Sequence[str], tokens: Sequence[str]) -> List[str]:
    if not tokens:
        return list(repos)

    filtered = list(repos)
    for token in tokens:
        lowered = token.lower()
        filtered = [repo for repo in filtered if lowered in os.path.basename(repo).lower()]
    return filtered


def pick_with_fzf(options: Sequence[str], root: str) -> str | None:
    fzf = shutil.which("fzf")
    if not fzf:
        return None

    labels = "\n".join(format_repo(repo, root) for repo in options)
    result = subprocess.run(
        [fzf],
        input=labels,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None

    selected = result.stdout.strip()
    if not selected:
        return None

    label_map = {
        format_repo(repo, root): repo
        for repo in options
    }
    return label_map.get(selected)


def pick_with_menu(options: Sequence[str], root: str) -> str:
    labels = [format_repo(repo, root) for repo in options]
    width = len(str(len(labels)))

    print("Available repositories:", file=sys.stderr)
    for idx, label in enumerate(labels, start=1):
        print(f"  {idx:>{width}}. {label}", file=sys.stderr)

    while True:
        sys.stderr.write(
            f"Select repo [1-{len(labels)}] (blank to cancel): "
        )
        sys.stderr.flush()
        choice = sys.stdin.readline().strip()

        if not choice:
            print("Selection cancelled.", file=sys.stderr)
            sys.exit(1)

        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(labels):
                return options[index - 1]

        print("Invalid selection. Please enter a number from the list.", file=sys.stderr)


def choose_repo(repos: Sequence[str], tokens: Sequence[str], root: str) -> str:
    matches = filter_repos(repos, tokens)
    if not matches:
        print("No repositories match that query.", file=sys.stderr)
        sys.exit(1)

    if len(matches) == 1:
        return matches[0]

    selection = pick_with_fzf(matches, root)
    if selection:
        return selection

    return pick_with_menu(matches, root)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Locate git repositories under one or more root directories. "
            "Set GIT_GO_ROOTS (colon-separated paths) to scan multiple roots."
        )
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Optional filter tokens to narrow the repo list.",
    )
    parser.add_argument(
        "--root",
        default=os.path.expanduser(os.environ.get("GIT_GO_ROOT", "~/dev")),
        help=(
            "Single root directory to scan (default: %(default)s). "
            "Ignored when GIT_GO_ROOTS is set."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List repositories and exit.",
    )
    parser.add_argument(
        "--no-fzf",
        action="store_true",
        help="Disable fzf even if it is installed.",
    )
    parser.add_argument(
        "--cache-file",
        default=DEFAULT_CACHE_PATH,
        help=f"Cache file to speed up repo discovery (default: {DEFAULT_CACHE_PATH}).",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=None,
        help=(
            "Seconds before cache is considered stale. "
            "Passing this flag also persists the new default for future runs."
        ),
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Rebuild cache even if it is still fresh.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache entirely.",
    )
    return parser.parse_args(argv)


def load_cache(path: str) -> CacheData:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return {
                root: CacheEntry(
                    timestamp=entry["timestamp"],
                    repos=entry["repos"],
                    ttl=entry.get("ttl"),
                )
                for root, entry in data.items()
                if isinstance(entry, dict)
            }
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def save_cache(path: str, cache: CacheData) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    serializable: Dict[str, Dict[str, object]] = {}
    for root, entry in cache.items():
        payload: Dict[str, object] = {
            "timestamp": entry["timestamp"],
            "repos": entry["repos"],
        }
        ttl = entry.get("ttl")
        if ttl is not None:
            payload["ttl"] = ttl
        serializable[root] = payload
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(serializable, fh)


def get_cached_repos(cache: CacheData, root: str, ttl: int) -> List[str] | None:
    entry = cache.get(root)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > ttl:
        return None
    return entry["repos"]


def determine_effective_ttl(args: argparse.Namespace, entry: CacheEntry | None) -> int:
    if args.cache_ttl is not None:
        return args.cache_ttl
    if entry:
        cached_ttl = entry.get("ttl")
        if cached_ttl is not None:
            return cached_ttl
    return DEFAULT_CACHE_TTL


def resolve_roots(args: argparse.Namespace) -> List[str]:
    """Return a list of absolute, existing root directories to scan."""
    env_roots = os.environ.get("GIT_GO_ROOTS", "").strip()
    if env_roots:
        raw = [r.strip() for r in env_roots.split(":") if r.strip()]
    else:
        raw = [args.root]
    return [
        os.path.abspath(os.path.expanduser(r))
        for r in raw
        if os.path.isdir(os.path.expanduser(r))
    ]


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    roots = resolve_roots(args)
    if not roots:
        print("No valid root directories found.", file=sys.stderr)
        return 1

    # When scanning multiple roots, display paths relative to ~ so the user
    # can easily tell which tree each repo lives in (e.g. dev/foo vs
    # Documents/dev/bar).
    display_root = os.path.expanduser("~") if len(roots) > 1 else roots[0]

    cache_path = os.path.expanduser(args.cache_file)
    cache_data: CacheData = {}

    if not args.no_cache:
        cache_data = load_cache(cache_path)

    all_repos: List[str] = []

    for root in roots:
        cache_entry: CacheEntry | None = cache_data.get(root)
        effective_ttl = determine_effective_ttl(args, cache_entry)

        if not args.no_cache and args.cache_ttl is not None and cache_entry:
            if cache_entry.get("ttl") != args.cache_ttl:
                cache_entry["ttl"] = args.cache_ttl
                cache_data[root] = cache_entry
                save_cache(cache_path, cache_data)

        repos: List[str] | None = None
        if not args.no_cache and not args.refresh_cache:
            repos = get_cached_repos(cache_data, root, effective_ttl)

        if repos is None:
            repos = find_git_repos(root)
            if not args.no_cache:
                cache_data[root] = CacheEntry(
                    timestamp=time.time(),
                    repos=repos,
                    ttl=effective_ttl,
                )
                save_cache(cache_path, cache_data)

        all_repos.extend(repos)

    if not all_repos:
        roots_str = ", ".join(roots)
        print(f"No git repositories found under {roots_str}.", file=sys.stderr)
        return 1

    if args.list:
        for repo in all_repos:
            print(format_repo(repo, display_root))
        return 0

    if args.no_fzf:
        selection = pick_with_menu(filter_repos(all_repos, args.query), display_root)
    else:
        selection = choose_repo(all_repos, args.query, display_root)

    print(selection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
