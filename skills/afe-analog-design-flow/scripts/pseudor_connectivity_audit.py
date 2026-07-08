#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_TERMINALS = ("PSUB", "DNW", "PWELL", "A", "B")


def logical_lines(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    current = ""
    start_line = 0
    for idx, raw in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(("*", "//", "#")):
            continue
        if stripped.startswith("+"):
            current += " " + stripped[1:].strip()
            continue
        if current:
            lines.append((start_line, current))
        current = stripped
        start_line = idx
    if current:
        lines.append((start_line, current))
    return lines


def tokenize(line: str) -> list[str]:
    clean = line.replace("(", " ").replace(")", " ").replace(",", " ")
    return [tok for tok in clean.split() if tok]


def split_instance(tokens: list[str]) -> tuple[str, list[str], str, list[str]]:
    params_at = len(tokens)
    for idx, tok in enumerate(tokens):
        if "=" in tok:
            params_at = idx
            break
    head = tokens[:params_at]
    params = tokens[params_at:]
    if len(head) < 2:
        return (tokens[0] if tokens else "", [], "", params)
    inst = head[0]
    subckt = head[-1]
    nodes = head[1:-1]
    return inst, nodes, subckt, params


def is_pseudor_like(inst: str, subckt: str, line: str, filters: tuple[str, ...]) -> bool:
    hay = f"{inst} {subckt} {line}".lower()
    return any(filt.lower() in hay for filt in filters)


def classify_node(name: str) -> str:
    n = name.lower()
    if n in {"0", "gnd", "vss", "sub", "psub"}:
        return "ground/substrate-like"
    if n in {"vdd", "avdd", "dvdd", "vdda", "vdd1p2", "vdd18", "vdd_1v8"}:
        return "supply-like"
    if "dnw" in n or "deep" in n:
        return "dnw-like"
    if "pwell" in n or "pw" in n:
        return "pwell-like"
    if "vcm" in n or "vocm" in n:
        return "common-mode-like"
    return ""


def risk_notes(mapping: dict[str, str]) -> list[str]:
    notes: list[str] = []
    psub = mapping.get("PSUB", "")
    dnw = mapping.get("DNW", "")
    pwell = mapping.get("PWELL", "")
    if psub and classify_node(psub) != "ground/substrate-like":
        notes.append("PSUB is not ground/substrate-like; verify substrate intent.")
    if dnw:
        cls = classify_node(dnw)
        if cls == "ground/substrate-like":
            notes.append("DNW appears tied to ground/substrate; verify this is intentional.")
        elif not cls:
            notes.append("DNW is not obviously a DNW/supply/driver node; verify well-bias output.")
    if pwell:
        cls = classify_node(pwell)
        if cls == "ground/substrate-like":
            notes.append("PWELL appears tied to ground; verify this is not the old wrong connection.")
        elif not cls:
            notes.append("PWELL is not obviously a PWELL/common-mode node; verify driver sense input.")
    if dnw and pwell and dnw == pwell:
        notes.append("DNW and PWELL use the same node; verify this is intended.")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract pseudoR-like instance connectivity from a Spectre/SPICE-style netlist."
    )
    parser.add_argument("netlist", help="Netlist file to audit.")
    parser.add_argument(
        "--filter",
        action="append",
        default=["pseudor", "pseudo_r", "pr1", "pr2"],
        help="Case-insensitive substring used to select pseudoR-like instances. Can be repeated.",
    )
    parser.add_argument(
        "--terminal-order",
        default=",".join(DEFAULT_TERMINALS),
        help="Comma-separated assumed terminal order for mapping display.",
    )
    args = parser.parse_args()

    path = Path(args.netlist).resolve()
    if not path.exists():
        raise SystemExit(f"Missing netlist: {path}")

    terminals = tuple(part.strip() for part in args.terminal_order.split(",") if part.strip())
    rows: list[tuple[int, str, str, list[str], dict[str, str], list[str]]] = []

    for line_no, line in logical_lines(path):
        tokens = tokenize(line)
        if not tokens:
            continue
        inst, nodes, subckt, _params = split_instance(tokens)
        if not inst.lower().startswith("x"):
            continue
        if not is_pseudor_like(inst, subckt, line, tuple(args.filter)):
            continue
        mapping = {term: nodes[idx] for idx, term in enumerate(terminals) if idx < len(nodes)}
        rows.append((line_no, inst, subckt, nodes, mapping, risk_notes(mapping)))

    print(f"# pseudoR Connectivity Audit: {path.name}")
    print(f"- assumed terminal order: {', '.join(terminals)}")
    print(f"- selected instances: {len(rows)}")
    print()
    print("line\tinstance\tsubckt\tnode_count\tmapping\trisk_notes")
    for line_no, inst, subckt, nodes, mapping, notes in rows:
        mapping_text = "; ".join(f"{k}={v}" for k, v in mapping.items())
        note_text = " | ".join(notes)
        print(f"{line_no}\t{inst}\t{subckt}\t{len(nodes)}\t{mapping_text}\t{note_text}")

    if not rows:
        print("No pseudoR-like instances matched. Adjust --filter if needed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

