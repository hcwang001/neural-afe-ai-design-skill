#!/usr/bin/env python3
"""Evaluate AFE lifecycle gates without ever granting human approval.

The tool is deliberately read-only. It may report that a gate is ready for an
independent human approval, but it never writes state, creates signatures, or
changes a gate to ``approved``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from governance_common import (
    GovernanceBundle,
    GovernanceError,
    blocking_risk_errors,
    change_control_errors,
    compute_scope_digest,
    evaluate_controlling_metrics,
    list_or_empty,
    load_bundle,
    load_evidence_records,
    load_valid_waivers,
    manifest_identity_errors,
    mapping_or_empty,
    string_set,
    validate_approval,
    validate_gate_actor,
    validate_project_structure,
    validate_review,
)


def _future_artifact_errors(
    gate_id: str, records: list[Any], gate_state: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    for record in records:
        manifest = record.manifest
        evidence_id = manifest.get("evidence_id", record.path.name)
        errors.extend(f"{gate_id}:future_evidence_schema:{reason}" for reason in record.schema_errors)
        errors.extend(
            f"{gate_id}:future_evidence_provenance:{reason}"
            for reason in record.provenance_errors
        )
        if manifest.get("exploratory_only") is not True:
            errors.append(f"{gate_id}:future_artifact_not_exploratory:{evidence_id}")
        if manifest.get("promotion_eligible") is not False:
            errors.append(f"{gate_id}:future_artifact_marked_for_promotion:{evidence_id}")
    if gate_state.get("review_record"):
        errors.append(f"{gate_id}:future_gate_has_review_record")
    if gate_state.get("approval_record"):
        errors.append(f"{gate_id}:future_gate_has_approval_record")
    return errors


def evaluate_gate(
    bundle: GovernanceBundle,
    gate_id: str,
    *,
    predecessor_effectively_approved: bool,
    project_governance_valid: bool,
) -> dict[str, Any]:
    state = bundle.state
    gate_state = mapping_or_empty(state.get("gates")).get(gate_id)
    gate_definition = mapping_or_empty(bundle.gate_policy.get("gates")).get(gate_id)
    result: dict[str, Any] = {
        "gate_id": gate_id,
        "gate_name": gate_definition.get("name") if isinstance(gate_definition, dict) else None,
        "current_status": gate_state.get("status") if isinstance(gate_state, dict) else None,
        "suggested_status": "changes_required",
        "scope_digest": None,
        "mandatory_artifacts_missing": [],
        "valid_promotion_evidence_ids": [],
        "stale_evidence_ids": [],
        "errors": [],
        "warnings": [],
        "eligible_for_human_close": False,
        "effective_approved": False,
        "can_start_next_gate": False,
    }
    errors: list[str] = result["errors"]
    warnings: list[str] = result["warnings"]

    if not isinstance(gate_state, dict):
        errors.append(f"{gate_id}:gate_state_missing")
        return result
    if not isinstance(gate_definition, dict):
        errors.append(f"{gate_id}:gate_definition_missing")
        return result

    errors.extend(validate_gate_actor(gate_id, gate_state, bundle.authorization_policy))
    if not project_governance_valid:
        errors.append(f"{gate_id}:project_governance_invalid")
    records, load_errors = load_evidence_records(bundle, gate_id, gate_state)
    errors.extend(load_errors)
    result["scope_digest"] = compute_scope_digest(bundle, gate_id, records)

    predecessor = gate_definition.get("predecessor")
    predecessor_required = predecessor is not None
    predecessor_ok = (not predecessor_required) or predecessor_effectively_approved

    if not predecessor_ok:
        if gate_state.get("status") != "not_started":
            errors.append(
                f"{gate_id}:predecessor_not_human_approved:{predecessor}:state_must_be_not_started"
            )
        errors.extend(_future_artifact_errors(gate_id, records, gate_state))
        result["suggested_status"] = "not_started"
        return result

    if gate_state.get("status") == "not_started":
        errors.extend(_future_artifact_errors(gate_id, records, gate_state))
        result["suggested_status"] = (
            "in_progress" if project_governance_valid else "changes_required"
        )
        return result

    candidate_id = gate_state.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        errors.append(f"{gate_id}:candidate_id_missing")

    valid_waivers, waiver_errors = load_valid_waivers(bundle, gate_id, gate_state)
    errors.extend(waiver_errors)

    allowed_levels = string_set(
        mapping_or_empty(bundle.evidence_policy.get("promotion_level_by_gate")).get(
            gate_id
        )
    )
    proxy_policy = mapping_or_empty(bundle.evidence_policy.get("proxy_policy"))
    disallowed_proxy_kinds = string_set(
        proxy_policy.get("disallowed_proxy_kinds")
    )
    gate_number = int(gate_id[1:])
    proxy_cutoff = str(
        proxy_policy.get("disallow_for_transistor_promotion_from_gate", "G5")
    )
    try:
        proxy_cutoff_number = int(proxy_cutoff[1:]) if proxy_cutoff.startswith("G") else 0
    except ValueError:
        proxy_cutoff_number = 0

    valid_records = []
    seen_evidence_ids: set[str] = set()
    has_stale = False
    has_invalid_evidence = False
    for record in records:
        manifest = record.manifest
        evidence_id = str(manifest.get("evidence_id", record.path.name))
        exploratory = manifest.get("exploratory_only") is True
        promotion_eligible = manifest.get("promotion_eligible") is True

        if exploratory and promotion_eligible:
            errors.append(f"{gate_id}:exploratory_evidence_marked_for_promotion:{evidence_id}")
            has_invalid_evidence = True
        if exploratory or not promotion_eligible:
            continue

        if evidence_id in seen_evidence_ids:
            errors.append(f"{gate_id}:duplicate_promotion_evidence_id:{evidence_id}")
            has_invalid_evidence = True
        seen_evidence_ids.add(evidence_id)

        identity_errors = manifest_identity_errors(bundle, gate_id, gate_state, record)
        for message in identity_errors:
            errors.append(f"{gate_id}:{message}")
        if identity_errors:
            has_invalid_evidence = True

        if manifest.get("evidence_level") not in allowed_levels:
            errors.append(
                f"{gate_id}:evidence_level_not_allowed:{evidence_id}:{manifest.get('evidence_level')}"
            )
            has_invalid_evidence = True

        proxy_kinds = string_set(manifest.get("proxy_kinds"))
        if gate_number >= proxy_cutoff_number and (
            manifest.get("contains_functional_proxy") is True
            or proxy_kinds.intersection(disallowed_proxy_kinds)
        ):
            errors.append(f"{gate_id}:functional_proxy_cannot_promote:{evidence_id}")
            has_invalid_evidence = True

        if record.schema_errors:
            has_invalid_evidence = True
            errors.extend(
                f"{gate_id}:evidence_invalid:{evidence_id}:{reason}"
                for reason in record.schema_errors
            )
        if record.provenance_errors:
            has_invalid_evidence = True
            errors.extend(
                f"{gate_id}:evidence_invalid:{evidence_id}:{reason}"
                for reason in record.provenance_errors
            )
        if record.stale_reasons:
            has_stale = True
            result["stale_evidence_ids"].append(evidence_id)
            errors.extend(
                f"{gate_id}:evidence_stale:{evidence_id}:{reason}"
                for reason in record.stale_reasons
            )
        if (
            not identity_errors
            and not record.schema_errors
            and not record.provenance_errors
            and not record.stale_reasons
        ):
            valid_records.append(record)
            result["valid_promotion_evidence_ids"].append(evidence_id)

    artifact_types = {str(record.manifest.get("artifact_type")) for record in valid_records}
    mandatory = string_set(gate_definition.get("mandatory_artifacts"))
    missing = sorted(mandatory - artifact_types)
    result["mandatory_artifacts_missing"] = missing
    errors.extend(f"{gate_id}:mandatory_artifact_missing:{name}" for name in missing)

    metric_errors, metric_notes = evaluate_controlling_metrics(
        bundle, gate_id, valid_records
    )
    errors.extend(metric_errors)
    warnings.extend(metric_notes)

    review_valid, review_errors, review_warnings, review_id = validate_review(
        bundle,
        gate_id,
        gate_state,
        str(result["scope_digest"]),
        valid_waivers,
    )
    errors.extend(review_errors)
    warnings.extend(review_warnings)

    risk_errors, risk_warnings = blocking_risk_errors(
        bundle, gate_id, gate_state, valid_waivers
    )
    errors.extend(risk_errors)
    warnings.extend(risk_warnings)
    eco_errors = change_control_errors(bundle, gate_id, gate_state)
    errors.extend(eco_errors)

    blocking_issue = any(
        token in message
        for message in errors
        for token in (
            "open_BLOCKER",
            "open_MAJOR",
            "risk_has_invalid_waiver",
            "finding_has_invalid_waiver",
            "outside_waiver_scope",
            "open_change_control",
        )
    )
    technical_error_prefixes = (
        "mandatory_artifact_missing",
        "controlling_metric_",
        "evidence_invalid",
        "evidence_level_not_allowed",
        "functional_proxy_cannot_promote",
        "evidence_project_id_mismatch",
        "evidence_candidate_id_mismatch",
        "evidence_gate_id_mismatch",
        "waiver:",
        "candidate_id_missing",
        "project_governance_invalid",
        "automation_actor_forbidden_state",
        "human_only_state_has_nonhuman_actor",
    )
    has_technical_errors = has_invalid_evidence or bool(missing) or bool(metric_errors) or bool(
        waiver_errors
    ) or any(any(prefix in message for prefix in technical_error_prefixes) for message in errors)

    eligible = (
        project_governance_valid
        and
        predecessor_ok
        and not has_stale
        and not has_technical_errors
        and not blocking_issue
        and review_valid
        and not risk_errors
        and not eco_errors
    )
    result["eligible_for_human_close"] = eligible

    if gate_state.get("status") == "human_approval_required" and not eligible:
        errors.append(f"{gate_id}:human_approval_required_state_without_readiness")
    if gate_state.get("status") == "review_ready" and (has_stale or has_technical_errors):
        errors.append(f"{gate_id}:review_ready_state_with_invalid_evidence")

    approval_valid = False
    if gate_state.get("status") == "approved":
        approval_valid, approval_errors = validate_approval(
            bundle,
            gate_id,
            gate_state,
            str(result["scope_digest"]),
            review_id,
        )
        errors.extend(approval_errors)
        if not eligible:
            errors.append(f"{gate_id}:approved_state_without_gate_readiness")
        result["effective_approved"] = eligible and approval_valid
    elif gate_state.get("approval_record"):
        warnings.append(f"{gate_id}:approval_record_present_but_state_not_approved")

    result["can_start_next_gate"] = result["effective_approved"]

    if result["effective_approved"]:
        # A verified approval is an observation only. No automated state
        # transition is recommended for a human-controlled approved record.
        result["suggested_status"] = None
    elif has_stale:
        result["suggested_status"] = "stale"
    elif blocking_issue or risk_errors or eco_errors:
        result["suggested_status"] = "blocked"
    elif has_technical_errors:
        result["suggested_status"] = "changes_required"
    elif not review_valid:
        result["suggested_status"] = "review_ready"
    elif eligible:
        result["suggested_status"] = "human_approval_required"
    else:
        result["suggested_status"] = "in_progress"
    return result


def evaluate_project(bundle: GovernanceBundle) -> dict[str, Any]:
    global_errors = validate_project_structure(bundle)
    governance_valid = not global_errors
    results: dict[str, dict[str, Any]] = {}
    expected_order = [f"G{index}" for index in range(11)]
    configured_order = list_or_empty(bundle.gate_policy.get("gate_order"))
    gate_order = configured_order if configured_order == expected_order else expected_order
    for gate_id in gate_order:
        gate_definition = mapping_or_empty(
            mapping_or_empty(bundle.gate_policy.get("gates")).get(gate_id)
        )
        predecessor = gate_definition.get("predecessor")
        predecessor_approved = True
        if predecessor is not None:
            predecessor_approved = bool(
                results.get(str(predecessor), {}).get("effective_approved")
            )
        results[gate_id] = evaluate_gate(
            bundle,
            str(gate_id),
            predecessor_effectively_approved=predecessor_approved,
            project_governance_valid=governance_valid,
        )
    return {
        "project_id": bundle.state.get("project_id"),
        "state_revision": bundle.state.get("state_revision"),
        "global_errors": global_errors,
        "gates": results,
    }


def _print_text(report: dict[str, Any], selected_gate: str | None) -> None:
    print(f"# AFE Gatekeeper: {report.get('project_id')}")
    if report.get("global_errors"):
        print("\nGlobal errors:")
        for error in report["global_errors"]:
            print(f"- {error}")
    gate_ids = [selected_gate] if selected_gate else list(report.get("gates", {}))
    for gate_id in gate_ids:
        gate = report.get("gates", {}).get(gate_id)
        if gate is None:
            print(f"\n## {gate_id}\n- ERROR: unknown gate")
            continue
        print(f"\n## {gate_id} - {gate.get('gate_name')}")
        print(f"- current_status: {gate.get('current_status')}")
        print(f"- suggested_status: {gate.get('suggested_status')}")
        print(f"- scope_digest: {gate.get('scope_digest')}")
        print(f"- eligible_for_human_close: {gate.get('eligible_for_human_close')}")
        print(f"- effective_approved: {gate.get('effective_approved')}")
        print(f"- can_start_next_gate: {gate.get('can_start_next_gate')}")
        for error in gate.get("errors", []):
            print(f"- ERROR: {error}")
        for warning in gate.get("warnings", []):
            print(f"- NOTE: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only AFE gate evaluator. Reports readiness but never writes "
            "approved state or human signatures."
        )
    )
    parser.add_argument("--state", required=True, help="Project state YAML/JSON path.")
    parser.add_argument("--gate", help="Evaluate/report one gate (predecessors are still checked).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    try:
        bundle = load_bundle(Path(args.state))
        report = evaluate_project(bundle)
    except GovernanceError as exc:
        if args.json:
            print(json.dumps({"fatal_error": str(exc)}, indent=2))
        else:
            print(f"FATAL: {exc}")
        return 2

    if args.gate and args.gate not in report.get("gates", {}):
        report.setdefault("global_errors", []).append(f"unknown_gate:{args.gate}")

    if args.json:
        output = report if not args.gate else {
            "project_id": report.get("project_id"),
            "state_revision": report.get("state_revision"),
            "global_errors": report.get("global_errors"),
            "gate": report.get("gates", {}).get(args.gate),
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        _print_text(report, args.gate)

    if report.get("global_errors"):
        return 1
    selected = [args.gate] if args.gate else list(report.get("gates", {}))
    for gate_id in selected:
        gate = report.get("gates", {}).get(gate_id, {})
        if gate.get("errors"):
            return 1
        if args.gate and not (
            gate.get("eligible_for_human_close") or gate.get("effective_approved")
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
