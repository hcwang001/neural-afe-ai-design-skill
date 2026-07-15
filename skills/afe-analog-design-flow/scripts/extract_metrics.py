#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def fmt_range(rows: list[dict[str, str]], key: str, unit: str = "") -> str:
    vals: list[float] = []
    for row in rows:
        value = row.get(key, "")
        if value not in ("", None):
            try:
                vals.append(float(value))
            except ValueError as exc:
                raise ValueError(f"Non-numeric value for {key}: {value!r}") from exc
    if not vals:
        return "n/a"
    suffix = f" {unit}" if unit else ""
    return f"{min(vals):.4g}..{max(vals):.4g}{suffix}"


def find_file(run_dir: Path, name: str) -> Path | None:
    candidate = run_dir / name
    if candidate.exists():
        return candidate
    matches = sorted(run_dir.rglob(name))
    if len(matches) > 1:
        raise RuntimeError(f"Ambiguous metric source {name}: {len(matches)} matches")
    return matches[0] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract compact AFE metrics from run CSVs.")
    parser.add_argument("run_dir", help="Analysis run directory.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        raise SystemExit(f"Missing run directory: {run_dir}")

    try:
        det_summary = find_file(run_dir, "det_summary.csv")
        det_dc = find_file(run_dir, "det_dc_rows.csv")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"# Metrics: {run_dir.name}")
    if det_summary:
        rows = read_csv(det_summary)
        for row in rows:
            module = row.get("module", "module")
            print(f"\n## {module}")
            for key, unit in [
                ("gain_1k_min_db", "dB"),
                ("gain_1k_max_db", "dB"),
                ("noise_300_10k_min_uVrms", "uVrms"),
                ("noise_300_10k_max_uVrms", "uVrms"),
                ("cmrr_1k_min_db", "dB"),
                ("psrr_vdd_rel_1k_min_db", "dB"),
                ("fhp_min_hz", "Hz"),
                ("fhp_max_hz", "Hz"),
                ("flp_min_hz", "Hz"),
                ("flp_max_hz", "Hz"),
            ]:
                if key in row and row[key] != "":
                    try:
                        parsed = float(row[key])
                    except ValueError as exc:
                        raise SystemExit(
                            f"Non-numeric value in {det_summary} for {key}: {row[key]!r}"
                        ) from exc
                    print(f"- {key}: {parsed:.4g} {unit}")

    if det_dc:
        rows = read_csv(det_dc)
        fullchain = [row for row in rows if row.get("module") == "fullchain"]
        if fullchain:
            print("\n## fullchain DC")
            try:
                print(f"- power_uW: {fmt_range(fullchain, 'power_uW', 'uW')}")
                print(f"- muxcm_v: {fmt_range(fullchain, 'muxcm_v', 'V')}")
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
