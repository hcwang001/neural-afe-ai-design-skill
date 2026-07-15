#!/usr/bin/env python3
"""Compare evidence dependency fingerprints with the current project baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from governance_common import (
    GovernanceError,
    load_bundle,
    load_evidence_records,
    validate_project_structure,
)


def check_staleness(state_path: Path, selected_gate: str | None = None) -> dict:
    bundle = load_bundle(state_path)
    report = {
        "project_id": bundle.state.get("project_id"),
        "errors": validate_project_structure(bundle),
        "evidence": [],
    }
    gate_ids = [selected_gate] if selected_gate else bundle.gate_policy.get("gate_order", [])
    for gate_id in gate_ids:
        gate_state = bundle.state.get("gates", {}).get(gate_id)
        if not isinstance(gate_state, dict):
            report["errors"].append(f"gate_state_missing:{gate_id}")
            continue
        records, load_errors = load_evidence_records(bundle, gate_id, gate_state)
        report["errors"].extend(load_errors)
        for record in records:
            promotion = bool(record.manifest.get("promotion_eligible")) and not bool(
                record.manifest.get("exploratory_only")
            )
            report["evidence"].append(
                {
                    "gate_id": gate_id,
                    "evidence_id": record.manifest.get("evidence_id"),
                    "promotion_evidence": promotion,
                    "stale": bool(record.stale_reasons),
                    "reasons": list(record.stale_reasons),
                    "validation_errors": list(record.schema_errors)
                    + list(record.provenance_errors),
                }
            )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AFE evidence freshness dependencies.")
    parser.add_argument("--state", required=True)
    parser.add_argument("--gate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = check_staleness(Path(args.state), args.gate)
    except GovernanceError as exc:
        print(json.dumps({"fatal_error": str(exc)}, indent=2) if args.json else f"FATAL: {exc}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"# AFE Stale Evidence Check: {report['project_id']}")
        for error in report["errors"]:
            print(f"- ERROR: {error}")
        for item in report["evidence"]:
            status = "STALE" if item["stale"] else "CURRENT"
            role = "promotion" if item["promotion_evidence"] else "exploratory/non-promotion"
            print(f"- {item['gate_id']} {item['evidence_id']}: {status} ({role})")
            for reason in item["reasons"]:
                print(f"  - {reason}")
            for error in item["validation_errors"]:
                print(f"  - INVALID: {error}")
    failed = bool(report["errors"]) or any(
        (item["stale"] and item["promotion_evidence"])
        or bool(item["validation_errors"])
        for item in report["evidence"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
