#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".csv", ".md", ".txt", ".log", ".yaml", ".yml"}


@dataclass(frozen=True)
class InventoryRule:
    name: str
    filename_terms: tuple[str, ...]
    content_terms: tuple[str, ...] = ()
    note: str = ""


INVENTORY_RULES = [
    InventoryRule("handoff-like files", ("handoff",), ("current phase", "next step")),
    InventoryRule("report-like files", ("report", "summary"), ("key metrics", "topology")),
    InventoryRule("netlist/wrapper-like files", ("netlist", "wrapper", ".scs", ".sp", ".cir", ".net")),
    InventoryRule("module-report-like files", ("module_report", "stage1_report", "stage2_report", "cmfb_report", "wellbias_report"), ("module report",)),
    InventoryRule("result-image-like files", ("module_result", "module_plot", "stage1", "stage2", "cmfb", "wellbias", "pseudor", ".png", ".svg")),
    InventoryRule("dc/pvt-like files", ("dc", "pvt", "det_dc_rows"), ("operating", "corner")),
    InventoryRule("gain/bandwidth-like files", ("gain", "bandwidth", "gbw", "ac")),
    InventoryRule("noise-like files", ("noise",)),
    InventoryRule("cmrr-like files", ("cmrr",)),
    InventoryRule("psrr-like files", ("psrr",)),
    InventoryRule("mismatch-like files", ("mismatch", "cinp", "deterministic"), ("mismatch",)),
    InventoryRule("startup/recovery-like files", ("startup", "recovery", "transient"), ("startup", "recovery")),
    InventoryRule("stability-like files", ("stb", "diffstb", "stability"), ("diffstbprobe", "phase margin")),
    InventoryRule("area/comparison-like files", ("area", "comparison"), ("area basis",)),
    InventoryRule("floorplan/layout-like files", ("floorplan", "layout"), ("floorplan", "layout")),
    InventoryRule("tapeout-readiness-like files", ("tapeout", "readiness"), ("tapeout readiness", "reliability")),
    InventoryRule("functional-ideal-audit-like files", ("ideal", "audit"), ("functional ideal", "behavioral source")),
    InventoryRule("monte-carlo-like files", ("mc", "monte", "monte-carlo"), ("monte", "sample count")),
    InventoryRule("pex/post-layout-like files", ("pex", "post-layout", "postlayout"), ("pex", "extraction")),
    InventoryRule("test/trim/calibration-like files", ("trim", "calibration", "test"), ("trim", "calibration")),
    InventoryRule("esd/top-level-like files", ("esd", "pad", "top-level"), ("esd", "pad")),
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


def matches(check: InventoryRule, files: list[Path], texts: dict[Path, str]) -> list[Path]:
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
        description=(
            "Non-authoritative file inventory for an AFE run directory. This tool "
            "does not validate metrics, provenance, freshness, review, or gate state."
        )
    )
    parser.add_argument("run_dir", nargs="?", default=".", help="Candidate report/run directory.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Deprecated compatibility flag. Inventory output never establishes gate readiness.",
    )
    parser.add_argument("--max-hits", type=int, default=4, help="Maximum paths shown per check.")
    args = parser.parse_args()

    root = Path(args.run_dir).resolve()
    if not root.exists():
        raise SystemExit(f"Missing run directory: {root}")

    files = iter_files(root)
    texts = {path: read_text(path) for path in files}

    print(f"# Non-Authoritative Evidence Inventory: {root.name}")
    print(f"- root: {root}")
    print(f"- files scanned: {len(files)}")
    print("- authoritative: false")
    print("- warning: filename/content hits are discovery hints, not evidence or gate status")
    print("- gate evaluation: use scripts/gatekeeper.py with machine-readable manifests")
    if args.strict:
        print("- deprecated: --strict has no gate meaning and is ignored")

    observed = 0
    for check in INVENTORY_RULES:
        hits = matches(check, files, texts)
        status = "OBSERVED" if hits else "not-observed"
        observed += bool(hits)
        print(f"\n- {check.name}: {status}")
        if check.note:
            print(f"    note: {check.note}")
        for hit in hits[: args.max_hits]:
            print(f"    - {rel(hit, root)}")
        if len(hits) > args.max_hits:
            print(f"    - ... {len(hits) - args.max_hits} more")
    print("\n# Summary")
    print(f"- categories observed: {observed}/{len(INVENTORY_RULES)}")
    print("- readiness conclusion: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
