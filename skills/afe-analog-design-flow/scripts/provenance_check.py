#!/usr/bin/env python3
"""Validate AFE evidence provenance and artifact integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from governance_common import (
    GovernanceError,
    load_bundle,
    load_evidence_records,
    manifest_identity_errors,
    validate_project_structure,
)


def check_provenance(state_path: Path, selected_gate: str | None = None) -> dict:
    bundle = load_bundle(state_path)
    report = {
        "project_id": bundle.state.get("project_id"),
        "global_errors": validate_project_structure(bundle),
        "evidence": [],
    }
    gate_ids = [selected_gate] if selected_gate else bundle.gate_policy.get("gate_order", [])
    for gate_id in gate_ids:
        gate_state = bundle.state.get("gates", {}).get(gate_id)
        if not isinstance(gate_state, dict):
            report["global_errors"].append(f"gate_state_missing:{gate_id}")
            continue
        records, load_errors = load_evidence_records(bundle, gate_id, gate_state)
        report["global_errors"].extend(load_errors)
        for record in records:
            identity_errors = manifest_identity_errors(bundle, gate_id, gate_state, record)
            errors = list(record.schema_errors) + list(record.provenance_errors) + identity_errors
            report["evidence"].append(
                {
                    "gate_id": gate_id,
                    "evidence_id": record.manifest.get("evidence_id"),
                    "manifest": str(record.path),
                    "promotion_eligible": record.manifest.get("promotion_eligible"),
                    "exploratory_only": record.manifest.get("exploratory_only"),
                    "valid_provenance": not errors,
                    "errors": errors,
                }
            )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AFE evidence provenance and digests.")
    parser.add_argument("--state", required=True)
    parser.add_argument("--gate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = check_provenance(Path(args.state), args.gate)
    except GovernanceError as exc:
        print(json.dumps({"fatal_error": str(exc)}, indent=2) if args.json else f"FATAL: {exc}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"# AFE Provenance Check: {report['project_id']}")
        for error in report["global_errors"]:
            print(f"- ERROR: {error}")
        for item in report["evidence"]:
            status = "VALID" if item["valid_provenance"] else "INVALID"
            print(f"- {item['gate_id']} {item['evidence_id']}: {status}")
            for error in item["errors"]:
                print(f"  - {error}")
    failed = bool(report["global_errors"]) or any(
        not item["valid_provenance"] for item in report["evidence"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
