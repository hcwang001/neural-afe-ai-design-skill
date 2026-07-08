#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


PATTERNS = [
    "CURRENT_THREAD_HANDOFF_*.md",
    "CURRENT_THREAD_HANDOFF.md",
    "*HANDOFF*.md",
]


def score(path: Path) -> tuple[int, float, str]:
    name = path.name
    dated = 1 if name.startswith("CURRENT_THREAD_HANDOFF_") else 0
    current = 1 if name == "CURRENT_THREAD_HANDOFF.md" else 0
    return (dated, current, path.stat().st_mtime, name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find likely current AFE handoff files.")
    parser.add_argument("root", nargs="?", default=".", help="Project root to scan.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum files to print.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seen: set[Path] = set()
    found: list[Path] = []
    for pattern in PATTERNS:
        for path in root.rglob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                found.append(path)

    found.sort(key=score, reverse=True)
    for path in found[: args.limit]:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        print(f"{rel}\t{path.stat().st_size} bytes")
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
