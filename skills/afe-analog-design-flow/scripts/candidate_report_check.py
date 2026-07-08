#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".csv", ".md", ".txt", ".log", ".yaml", ".yml"}


@dataclass(frozen=True)
class Check:
    name: str
    required: bool
    filename_terms: tuple[str, ...]
    content_terms: tuple[str, ...] = ()
    note: str = ""


CHECKS = [
    Check("handoff", True, ("handoff",), ("current phase", "next step")),
    Check("candidate report", True, ("report", "summary"), ("key metrics", "topology")),
    Check("source netlist/wrapper", True, ("netlist", "wrapper", ".scs", ".sp", ".cir", ".net")),
    Check("module-level reports", True, ("module_report", "stage1_report", "stage2_report", "cmfb_report", "wellbias_report"), ("module report",)),
    Check("module-level result images", True, ("module_result", "module_plot", "stage1", "stage2", "cmfb", "wellbias", "pseudor", ".png", ".svg")),
    Check("dc/pvt evidence", True, ("dc", "pvt", "det_dc_rows"), ("operating", "corner")),
    Check("gain/bandwidth evidence", True, ("gain", "bandwidth", "gbw", "ac")),
    Check("noise evidence", True, ("noise",)),
    Check("cmrr evidence", True, ("cmrr",)),
    Check("psrr evidence", True, ("psrr",)),
    Check("mismatch evidence", True, ("mismatch", "cinp", "deterministic"), ("mismatch",)),
    Check("startup/recovery evidence", True, ("startup", "recovery", "transient"), ("startup", "recovery")),
    Check("stability evidence", True, ("stb", "diffstb", "stability"), ("diffstbprobe", "phase margin")),
    Check("area/comparison", True, ("area", "comparison"), ("area basis",)),
    Check("floorplan/layout suggestion", True, ("floorplan", "layout"), ("floorplan", "layout")),
    Check("tapeout readiness", True, ("tapeout", "readiness"), ("tapeout readiness", "reliability")),
    Check("functional ideal audit", True, ("ideal", "audit"), ("functional ideal", "behavioral source")),
    Check("monte carlo", False, ("mc", "monte", "monte-carlo"), ("monte", "sample count")),
    Check("pex/post-layout plan", False, ("pex", "post-layout", "postlayout"), ("pex", "extraction")),
    Check("test/trim/calibration plan", False, ("trim", "calibration", "test"), ("trim", "calibration")),
    Check("esd/top-level plan", False, ("esd", "pad", "top-level"), ("esd", "pad")),
]


def iter_files(root: Path) -> list[Path]:
    ignored = {".git", "__pycache__", "psf", "raw"}
    found: list[Path] = []
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file():
            found.append(path)
    return found


def read_text(path: Path) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def matches(check: Check, files: list[Path], texts: dict[Path, str]) -> list[Path]:
    hits: list[Path] = []
    for path in files:
        name = path.name.lower()
        suffix = path.suffix.lower()
        filename_hit = any(term in name or term == suffix for term in check.filename_terms)
        content_hit = False
        if check.content_terms:
            text = texts.get(path, "")
            content_hit = any(term.lower() in text for term in check.content_terms)
        if filename_hit or content_hit:
            hits.append(path)
    return hits


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether an AFE candidate report directory has expected evidence artifacts."
    )
    parser.add_argument("run_dir", nargs="?", default=".", help="Candidate report/run directory.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when required checks are missing.")
    parser.add_argument("--max-hits", type=int, default=4, help="Maximum paths shown per check.")
    args = parser.parse_args()

    root = Path(args.run_dir).resolve()
    if not root.exists():
        raise SystemExit(f"Missing run directory: {root}")

    files = iter_files(root)
    texts = {path: read_text(path) for path in files}

    print(f"# Candidate Report Check: {root.name}")
    print(f"- root: {root}")
    print(f"- files scanned: {len(files)}")

    missing_required: list[str] = []
    missing_optional: list[str] = []

    for check in CHECKS:
        hits = matches(check, files, texts)
        status = "FOUND" if hits else ("MISSING" if check.required else "optional-missing")
        marker = "[x]" if hits else ("[!]" if check.required else "[-]")
        print(f"\n{marker} {check.name}: {status}")
        if check.note:
            print(f"    note: {check.note}")
        for hit in hits[: args.max_hits]:
            print(f"    - {rel(hit, root)}")
        if len(hits) > args.max_hits:
            print(f"    - ... {len(hits) - args.max_hits} more")
        if not hits and check.required:
            missing_required.append(check.name)
        elif not hits:
            missing_optional.append(check.name)

    print("\n# Summary")
    print(f"- missing required: {len(missing_required)}")
    if missing_required:
        print("  " + ", ".join(missing_required))
    print(f"- missing optional: {len(missing_optional)}")
    if missing_optional:
        print("  " + ", ".join(missing_optional))

    return 1 if args.strict and missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
