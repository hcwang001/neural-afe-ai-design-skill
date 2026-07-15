#!/usr/bin/env python3
"""Shared, fail-closed governance primitives for the AFE lifecycle tools."""

from __future__ import annotations

import hashlib
import json
import math
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - exercised only on incomplete installs
    InvalidSignature = Exception
    Ed25519PublicKey = None

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on incomplete installs
    yaml = None

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover - exercised only on incomplete installs
    Draft202012Validator = None
    FormatChecker = None
    SchemaError = Exception


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "governance" / "schemas"
SCRIPT_DIR = Path(__file__).resolve().parent


class GovernanceError(RuntimeError):
    """Raised when a governance input cannot be parsed safely."""


@dataclass(frozen=True)
class EvidenceRecord:
    path: Path
    manifest: dict[str, Any]
    schema_errors: tuple[str, ...]
    provenance_errors: tuple[str, ...]
    stale_reasons: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceBundle:
    state_path: Path
    state: dict[str, Any]
    gate_policy: dict[str, Any]
    evidence_policy: dict[str, Any]
    authorization_policy: dict[str, Any]
    requirements: dict[str, Any]
    risk_register: dict[str, Any]
    trusted_signers: dict[str, Any]


def load_data(path: Path) -> dict[str, Any]:
    """Load JSON or YAML and require an object at the document root."""

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GovernanceError(f"cannot read {path}: {exc}") from exc

    data: Any
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        if yaml is None:
            raise GovernanceError(
                f"{path} is not JSON and PyYAML is unavailable; install PyYAML>=6"
            )
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise GovernanceError(f"cannot parse {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise GovernanceError(f"{path} must contain a mapping/object at the root")
    return data


def resolve_ref(owner_path: Path, reference: str) -> Path:
    path = Path(reference)
    if not path.is_absolute():
        path = owner_path.parent / path
    return path.resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def canonical_digest(value: Any) -> str:
    def non_json_value(item: Any) -> dict[str, str]:
        return {
            "__unsupported_json_type__": type(item).__name__,
            "value": str(item),
        }

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=non_json_value,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def dotted_get(mapping: dict[str, Any], dotted_path: str) -> Any:
    current: Any = mapping
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def mapping_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def string_set(value: Any) -> set[str]:
    return {item for item in list_or_empty(value) if isinstance(item, str)}


def mapping_keys(value: Any) -> set[str]:
    return {str(key) for key in value} if isinstance(value, dict) else set()


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_schema(
    instance: dict[str, Any], schema_filename: str, label: str
) -> list[str]:
    """Validate an instantiated governance record against Draft 2020-12.

    Schema validation is a fail-closed runtime control, not a documentation-only
    check. Generic templates may contain REPLACE_WITH placeholders and are not
    considered instantiated records until those placeholders are resolved.
    """

    if Draft202012Validator is None or FormatChecker is None:
        return [f"{label}:jsonschema_dependency_unavailable"]
    schema_path = SCHEMA_DIR / schema_filename
    try:
        schema = load_data(schema_path)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
    except (GovernanceError, SchemaError) as exc:
        return [f"{label}:schema_unusable:{schema_filename}:{exc}"]

    errors: list[str] = []
    for error in sorted(
        validator.iter_errors(instance),
        key=lambda item: [str(part) for part in item.path],
    ):
        location = "$"
        for part in error.absolute_path:
            location += f"[{part}]" if isinstance(part, int) else f".{part}"
        errors.append(f"{label}:schema_violation:{location}:{error.message}")
    return errors


def load_bundle(state_path: Path) -> GovernanceBundle:
    state_path = state_path.resolve()
    state = load_data(state_path)
    policies = state.get("policies")
    if not isinstance(policies, dict):
        raise GovernanceError("project state is missing policies")

    required_policy_refs = ("gate_policy", "evidence_policy", "authorization_policy")
    missing_refs = [name for name in required_policy_refs if not policies.get(name)]
    if missing_refs:
        raise GovernanceError(f"project state is missing policy references: {missing_refs}")

    gate_policy = load_data(resolve_ref(state_path, str(policies["gate_policy"])))
    evidence_policy = load_data(resolve_ref(state_path, str(policies["evidence_policy"])))
    authorization_policy = load_data(
        resolve_ref(state_path, str(policies["authorization_policy"]))
    )

    requirements_ref = state.get("requirements_traceability")
    risk_ref = state.get("risk_register")
    signers_ref = state.get("trusted_signers")
    if not isinstance(requirements_ref, str) or not requirements_ref:
        raise GovernanceError("project state is missing requirements_traceability")
    if not isinstance(risk_ref, str) or not risk_ref:
        raise GovernanceError("project state is missing risk_register")
    if not isinstance(signers_ref, str) or not signers_ref:
        raise GovernanceError("project state is missing trusted_signers")

    requirements = load_data(resolve_ref(state_path, requirements_ref))
    risk_register = load_data(resolve_ref(state_path, risk_ref))
    trusted_signers = load_data(resolve_ref(state_path, signers_ref))
    return GovernanceBundle(
        state_path=state_path,
        state=state,
        gate_policy=gate_policy,
        evidence_policy=evidence_policy,
        authorization_policy=authorization_policy,
        requirements=requirements,
        risk_register=risk_register,
        trusted_signers=trusted_signers,
    )


def governance_contract_hash(
    gate_policy: dict[str, Any],
    evidence_policy: dict[str, Any],
    authorization_policy: dict[str, Any],
) -> str:
    schemas = {
        path.name: load_data(path)
        for path in sorted(SCHEMA_DIR.glob("*.schema.json"))
    }
    engine_names = (
        "governance_common.py",
        "gatekeeper.py",
        "provenance_check.py",
        "stale_evidence_check.py",
    )
    try:
        engine_files = {
            name: sha256_file(SCRIPT_DIR / name)
            for name in engine_names
        }
    except OSError as exc:
        raise GovernanceError(f"cannot hash governance engine: {exc}") from exc
    return canonical_digest(
        {
            "gate_policy": gate_policy,
            "evidence_policy": evidence_policy,
            "authorization_policy": authorization_policy,
            "schemas": schemas,
            "governance_engine": engine_files,
        }
    )


def policy_bundle_hash(bundle: GovernanceBundle) -> str:
    return governance_contract_hash(
        bundle.gate_policy,
        bundle.evidence_policy,
        bundle.authorization_policy,
    )


def validate_policy_contract(bundle: GovernanceBundle) -> list[str]:
    """Reject a policy bundle that weakens or invents unimplemented controls."""

    errors: list[str] = []
    gate_policy = bundle.gate_policy
    evidence_policy = bundle.evidence_policy
    authorization = bundle.authorization_policy

    required_readiness = {
        "mandatory_artifacts_valid",
        "controlling_requirements_satisfied",
        "no_open_blocker_or_major",
        "provenance_current",
        "evidence_not_stale",
        "predecessor_effectively_approved",
        "waivers_valid_and_unexpired",
        "independent_review_completed",
    }
    required_effective = {"human_close_eligible", "verified_human_approval"}
    contract = mapping_or_empty(gate_policy.get("criteria_contract"))
    if string_set(contract.get("human_close_eligible_requires")) != required_readiness:
        errors.append("gate_policy_readiness_contract_mismatch")
    if string_set(contract.get("effective_approved_requires")) != required_effective:
        errors.append("gate_policy_effective_approval_contract_mismatch")

    gate_order = gate_policy.get("gate_order", [])
    gates = gate_policy.get("gates", {})
    if gate_order != [f"G{index}" for index in range(11)]:
        errors.append("gate_policy_order_must_be_G0_through_G10")
    if isinstance(gates, dict):
        critical_artifacts = {
            "G1": {
                "specification_baseline",
                "requirements_traceability",
                "electrode_interface_contract",
                "adc_interface_contract",
                "pmu_interface_contract",
                "top_level_interface_contract",
            },
            "G6": {
                "schematic_candidate_manifest",
                "full_chain_pvt_evidence",
                "metric_results",
                "monte_carlo_evidence",
                "mismatch_aware_rejection_evidence",
                "reliability_audit",
                "high_z_node_audit",
                "functional_ideal_audit",
            },
            "G7": {
                "layout_ready_manifest",
                "floorplan",
                "layout_constraints",
                "test_trim_calibration_plan",
                "esd_pad_plan",
                "interface_closure",
                "pex_plan",
            },
            "G8": {
                "pex_candidate_manifest",
                "drc_report",
                "lvs_report",
                "extraction_manifest",
                "pex_netlist",
            },
            "G9": {
                "post_layout_signoff_manifest",
                "post_layout_pvt_evidence",
                "post_layout_monte_carlo_evidence",
                "test_interface_verification",
                "esd_interface_verification",
                "post_fill_extraction_evidence",
            },
            "G10": {
                "tapeout_release_manifest",
                "layout_release_digest",
                "signoff_summary",
                "waiver_summary",
                "interface_release",
                "foundry_deck_manifest",
                "data_integrity_report",
            },
        }
        previous: str | None = None
        for gate_id in gate_order if isinstance(gate_order, list) else []:
            if not isinstance(gate_id, str):
                errors.append("gate_policy_gate_id_not_string")
                continue
            definition = gates.get(gate_id)
            if not isinstance(definition, dict):
                continue
            if definition.get("predecessor") != previous:
                errors.append(f"{gate_id}:gate_policy_predecessor_mismatch")
            expected_entry = (
                {"project_state_instantiated"}
                if previous is None
                else {"predecessor_effectively_approved"}
            )
            if string_set(definition.get("entry_criteria")) != expected_entry:
                errors.append(f"{gate_id}:gate_policy_entry_criteria_mismatch")
            if string_set(definition.get("exit_criteria")) != required_effective:
                errors.append(f"{gate_id}:gate_policy_exit_criteria_mismatch")
            if not isinstance(definition.get("mandatory_artifacts"), list) or not definition.get(
                "mandatory_artifacts"
            ):
                errors.append(f"{gate_id}:gate_policy_mandatory_artifacts_missing")
            elif not critical_artifacts.get(gate_id, set()).issubset(
                string_set(definition.get("mandatory_artifacts"))
            ):
                errors.append(f"{gate_id}:gate_policy_critical_artifacts_weakened")
            review_roles = string_set(definition.get("required_review_roles"))
            approval_roles = string_set(definition.get("required_approval_roles"))
            if not review_roles or not review_roles.issubset(
                string_set(
                    mapping_or_empty(authorization.get("review")).get("allowed_roles")
                )
            ):
                errors.append(f"{gate_id}:gate_policy_review_roles_invalid")
            if not approval_roles or not approval_roles.issubset(
                string_set(
                    mapping_or_empty(authorization.get("approval")).get("allowed_roles")
                )
            ):
                errors.append(f"{gate_id}:gate_policy_approval_roles_invalid")
            previous = str(gate_id)
        if string_set(gates.get("G9", {}).get("required_review_roles")) != {
            "signoff_reviewer"
        }:
            errors.append("G9:signoff_reviewer_required")
        if string_set(gates.get("G10", {}).get("required_review_roles")) != {
            "signoff_reviewer"
        }:
            errors.append("G10:signoff_reviewer_required")
        if string_set(gates.get("G10", {}).get("required_approval_roles")) != {
            "release_authority"
        }:
            errors.append("G10:release_authority_required")

    finding_policy = mapping_or_empty(gate_policy.get("finding_policy"))
    if string_set(finding_policy.get("blocking_open_severities")) != {"BLOCKER", "MAJOR"}:
        errors.append("gate_policy_blocking_severities_mismatch")
    if "BLOCKER" not in string_set(finding_policy.get("non_waivable_severities")):
        errors.append("gate_policy_BLOCKER_must_be_non_waivable")
    transition = mapping_or_empty(gate_policy.get("transition_policy"))
    if transition.get("require_predecessor_human_approval") is not True:
        errors.append("gate_policy_predecessor_human_approval_not_required")
    if transition.get("automated_close_allowed") is not False:
        errors.append("gate_policy_automated_close_must_be_false")
    if transition.get("future_gate_default_state") != "not_started":
        errors.append("gate_policy_future_gate_default_not_not_started")
    flags = mapping_or_empty(transition.get("parallel_artifact_flags"))
    if flags != {"exploratory_only": True, "promotion_eligible": False}:
        errors.append("gate_policy_parallel_artifact_flags_weakened")
    change_policy = mapping_or_empty(gate_policy.get("change_control"))
    if string_set(change_policy.get("blocking_statuses")) != {
        "proposed",
        "impact_assessed",
        "implemented",
        "revalidation_required",
        "verified",
    }:
        errors.append("gate_policy_change_control_statuses_mismatch")
    if string_set(change_policy.get("non_blocking_statuses")) != {"closed", "cancelled"}:
        errors.append("gate_policy_change_control_nonblocking_statuses_mismatch")
    if change_policy.get("bind_records_into_scope_digest") is not True:
        errors.append("gate_policy_change_records_not_scope_bound")

    permitted_automation_states = {
        "in_progress",
        "review_ready",
        "human_approval_required",
        "changes_required",
        "blocked",
        "stale",
    }
    configured_states = string_set(authorization.get("automation_allowed_gate_states"))
    if not configured_states.issubset(permitted_automation_states):
        errors.append("authorization_policy_automation_state_escape")
    if string_set(authorization.get("human_only_gate_states")) != {"approved"}:
        errors.append("authorization_policy_approved_not_human_only")
    if mapping_or_empty(authorization.get("signature")).get("supported_methods") != ["ed25519"]:
        errors.append("authorization_policy_signature_method_mismatch")
    for section in ("review", "approval", "waiver", "change"):
        if mapping_or_empty(authorization.get(section)).get("require_verified_signature") is not True:
            errors.append(f"authorization_policy_{section}_signature_not_required")
    if mapping_or_empty(authorization.get("approval")).get("require_distinct_from_reviewer") is not True:
        errors.append("authorization_policy_approver_reviewer_separation_missing")
    if mapping_or_empty(authorization.get("waiver")).get("require_distinct_from_owner") is not True:
        errors.append("authorization_policy_waiver_owner_separation_missing")

    required_all_provenance = {
        "source_commit",
        "evidence_commit",
        "spec_hash",
        "timestamp_utc",
        "policy_hash",
    }
    configured_all = string_set(
        mapping_or_empty(evidence_policy.get("required_provenance")).get("all")
    )
    if not required_all_provenance.issubset(configured_all):
        errors.append("evidence_policy_common_provenance_weakened")
    expected_levels = {
        "G0": {"analysis"},
        "G1": {"analysis"},
        "G2": {"analysis"},
        "G3": {"primitive"},
        "G4": {"behavioral", "transistor_schematic"},
        "G5": {"transistor_schematic"},
        "G6": {"transistor_schematic", "monte_carlo"},
        "G7": {"layout_planning", "transistor_schematic", "monte_carlo"},
        "G8": {"pex"},
        "G9": {"post_layout", "post_layout_monte_carlo"},
        "G10": {"release", "post_layout"},
    }
    promotion_levels = mapping_or_empty(evidence_policy.get("promotion_level_by_gate"))
    for gate_id, expected in expected_levels.items():
        if string_set(promotion_levels.get(gate_id)) != expected:
            errors.append(f"{gate_id}:evidence_policy_promotion_levels_mismatch")
    proxy_policy = mapping_or_empty(evidence_policy.get("proxy_policy"))
    if proxy_policy.get("disallow_for_transistor_promotion_from_gate") != "G5":
        errors.append("evidence_policy_proxy_cutoff_mismatch")
    required_by_level = mapping_or_empty(evidence_policy.get("required_provenance"))
    transistor_minimum = {
        "netlist_hash",
        "testbench_hash",
        "pdk.id",
        "pdk.release",
        "pdk.model_hash",
        "pdk.model_sections",
        "simulator.name",
        "simulator.version",
        "simulator.executable_hash",
        "command",
        "command_profile_hash",
        "metric_extractor_hash",
    }
    if not transistor_minimum.issubset(
        string_set(required_by_level.get("transistor_schematic"))
    ):
        errors.append("evidence_policy_transistor_provenance_weakened")
    mc_minimum = transistor_minimum | {
        "monte_carlo.seed",
        "monte_carlo.sample_count",
        "monte_carlo.statistical_section",
    }
    for level in ("monte_carlo", "post_layout_monte_carlo"):
        if not mc_minimum.issubset(string_set(required_by_level.get(level))):
            errors.append(f"evidence_policy_{level}_provenance_weakened")
    pex_minimum = transistor_minimum | {
        "layout_hash",
        "pex_hash",
        "extraction_deck_hash",
    }
    for level in ("pex", "post_layout"):
        if not pex_minimum.issubset(string_set(required_by_level.get(level))):
            errors.append(f"evidence_policy_{level}_provenance_weakened")
    if not (pex_minimum | mc_minimum).issubset(
        string_set(required_by_level.get("post_layout_monte_carlo"))
    ):
        errors.append("evidence_policy_post_layout_monte_carlo_physical_provenance_weakened")
    required_freshness = {
        "source_commit",
        "spec_hash",
        "netlist_hash",
        "testbench_hash",
        "metric_extractor_hash",
        "command_profile_hash",
        "policy_hash",
        "pdk.id",
        "pdk.release",
        "pdk.model_hash",
        "pdk.model_sections",
        "simulator.name",
        "simulator.version",
        "simulator.executable_hash",
    }
    configured_freshness = mapping_keys(evidence_policy.get("freshness_dependencies"))
    if not required_freshness.issubset(configured_freshness):
        errors.append("evidence_policy_freshness_dependencies_weakened")
    integrity = mapping_or_empty(evidence_policy.get("artifact_integrity"))
    if integrity.get("require_existing_file") is not True or integrity.get(
        "require_digest_match"
    ) is not True:
        errors.append("evidence_policy_artifact_integrity_weakened")
    if integrity.get("hash_algorithm") != "sha256":
        errors.append("evidence_policy_hash_algorithm_mismatch")
    if integrity.get("old_project_data_is_promotion_evidence") is not False:
        errors.append("evidence_policy_old_project_promotion_escape")
    if integrity.get("old_candidate_data_is_promotion_evidence") is not False:
        errors.append("evidence_policy_old_candidate_promotion_escape")
    metric_policy = mapping_or_empty(evidence_policy.get("metric_policy"))
    if metric_policy.get("fail_on_parse_error") is not True or metric_policy.get(
        "fail_on_missing_result"
    ) is not True:
        errors.append("evidence_policy_metric_fail_closed_disabled")
    return errors


def validate_project_structure(bundle: GovernanceBundle) -> list[str]:
    state = bundle.state
    errors: list[str] = validate_schema(
        state, "project-state.schema.json", "project_state"
    )
    errors.extend(
        validate_schema(
            bundle.trusted_signers,
            "trusted-signers.schema.json",
            "trusted_signers",
        )
    )
    errors.extend(
        validate_schema(
            bundle.requirements,
            "requirements-traceability.schema.json",
            "requirements_traceability",
        )
    )
    errors.extend(
        validate_schema(
            bundle.risk_register,
            "risk-register.schema.json",
            "risk_register",
        )
    )
    errors.extend(validate_policy_contract(bundle))
    required = (
        "schema_version",
        "project_id",
        "state_revision",
        "template_only",
        "current_baseline",
        "policies",
        "requirements_traceability",
        "risk_register",
        "trusted_signers",
        "decision_records",
        "change_records",
        "gates",
    )
    for key in required:
        if key not in state:
            errors.append(f"project_state_missing:{key}")
    if state.get("template_only") is not False:
        errors.append("project_state_is_template_only")
    if not isinstance(state.get("project_id"), str) or state.get("project_id", "").startswith(
        "REPLACE_"
    ):
        errors.append("project_id_not_instantiated")

    gates = state.get("gates")
    if not isinstance(gates, dict):
        errors.append("project_state_gates_not_mapping")
        return errors

    policy_gates = bundle.gate_policy.get("gates", {})
    gate_order = bundle.gate_policy.get("gate_order", [])
    if not isinstance(policy_gates, dict) or not isinstance(gate_order, list):
        errors.append("gate_policy_malformed")
        return errors
    for gate_id in gate_order:
        if not isinstance(gate_id, str):
            errors.append("gate_policy_gate_id_not_string")
            continue
        if gate_id not in gates:
            errors.append(f"project_state_missing_gate:{gate_id}")
        if gate_id not in policy_gates:
            errors.append(f"gate_policy_missing_definition:{gate_id}")

    baseline = state.get("current_baseline", {})
    if not isinstance(baseline, dict):
        errors.append("current_baseline_not_mapping")
    else:
        for key in (
            "source_commit",
            "spec_hash",
            "netlist_hash",
            "testbench_hash",
            "command_profile_hash",
            "metric_extractor_hash",
            "policy_hash",
            "pdk",
            "simulator",
        ):
            if dotted_get(baseline, key) in (None, ""):
                errors.append(f"current_baseline_missing:{key}")

    if bundle.requirements.get("project_id") != state.get("project_id"):
        errors.append("requirements_project_id_mismatch")
    if bundle.requirements.get("spec_hash") != dotted_get(baseline, "spec_hash"):
        errors.append("requirements_spec_hash_stale")
    if bundle.risk_register.get("project_id") != state.get("project_id"):
        errors.append("risk_register_project_id_mismatch")
    if bundle.trusted_signers.get("project_id") != state.get("project_id"):
        errors.append("trusted_signers_project_id_mismatch")
    if dotted_get(baseline, "policy_hash") != policy_bundle_hash(bundle):
        errors.append("current_baseline_policy_hash_mismatch")
    for field, schema_filename, id_field in (
        ("decision_records", "decision-record.schema.json", "decision_id"),
        ("change_records", "change-record.schema.json", "change_id"),
    ):
        records, record_errors = load_state_records(
            bundle, field, schema_filename, id_field
        )
        errors.extend(record_errors)
        for record in records:
            if record.get("project_id") != state.get("project_id"):
                errors.append(
                    f"{field}:{record.get(id_field, 'unknown')}:project_id_mismatch"
                )
    return errors


def load_state_records(
    bundle: GovernanceBundle,
    field: str,
    schema_filename: str,
    id_field: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Load and schema-check root-level decision or change-control records."""

    references = bundle.state.get(field, [])
    if not isinstance(references, list):
        return [], [f"project_state_{field}_not_list"]
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for reference in references:
        if not isinstance(reference, str) or not reference:
            errors.append(f"{field}:reference_invalid")
            continue
        try:
            record = load_data(resolve_ref(bundle.state_path, reference))
        except GovernanceError as exc:
            errors.append(f"{field}:record_unreadable:{reference}:{exc}")
            continue
        errors.extend(
            validate_schema(
                record,
                schema_filename,
                f"{field}:{record.get(id_field, reference)}",
            )
        )
        records.append(record)
    return records, errors


def validate_gate_actor(
    gate_id: str,
    gate_state: dict[str, Any],
    authorization_policy: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    status = gate_state.get("status")
    actor = gate_state.get("status_actor")
    if not isinstance(actor, dict):
        return [f"{gate_id}:status_actor_missing"]
    actor_type = actor.get("actor_type")
    if not actor.get("actor_id"):
        errors.append(f"{gate_id}:status_actor_id_missing")
    if parse_utc(actor.get("updated_at")) is None:
        errors.append(f"{gate_id}:status_actor_timestamp_invalid")

    automation = string_set(authorization_policy.get("automation_actor_types"))
    automation_states = string_set(
        authorization_policy.get("automation_allowed_gate_states")
    )
    human_only_states = string_set(authorization_policy.get("human_only_gate_states"))
    if actor_type in automation and status not in automation_states:
        errors.append(f"{gate_id}:automation_actor_forbidden_state:{status}")
    if status in human_only_states and actor_type != "human":
        errors.append(f"{gate_id}:human_only_state_has_nonhuman_actor:{actor_type}")
    return errors


def required_provenance_fields(
    evidence_level: str, evidence_policy: dict[str, Any]
) -> list[str]:
    required = evidence_policy.get("required_provenance", {})
    fields = (
        list(list_or_empty(required.get("all")))
        if isinstance(required, dict)
        else []
    )
    fields.extend(
        list_or_empty(required.get(evidence_level)) if isinstance(required, dict) else []
    )
    return list(dict.fromkeys(str(field) for field in fields))


def validate_provenance(
    manifest: dict[str, Any],
    manifest_path: Path,
    evidence_policy: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        return ["provenance_missing"]

    level = str(manifest.get("evidence_level", ""))
    for field in required_provenance_fields(level, evidence_policy):
        if dotted_get(provenance, field) in (None, "", []):
            errors.append(f"provenance_missing:{field}")

    if parse_utc(provenance.get("timestamp_utc")) is None:
        errors.append("provenance_timestamp_invalid_or_not_timezone_aware")

    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("artifact_record_missing")
        return errors
    artifact_ref = artifact.get("path")
    expected_hash = artifact.get("sha256")
    if not isinstance(artifact_ref, str) or not artifact_ref:
        errors.append("artifact_path_missing")
        return errors
    artifact_path = resolve_ref(manifest_path, artifact_ref)
    if not artifact_path.is_file():
        errors.append(f"artifact_file_missing:{artifact_ref}")
    elif not isinstance(expected_hash, str) or not expected_hash.startswith("sha256:"):
        errors.append("artifact_digest_missing_or_invalid")
    else:
        try:
            actual_hash = sha256_file(artifact_path)
        except OSError as exc:
            errors.append(f"artifact_file_unreadable:{artifact_ref}:{exc}")
        else:
            if actual_hash != expected_hash:
                errors.append(f"artifact_digest_mismatch:{expected_hash}:{actual_hash}")

    if manifest.get("status") != "valid":
        errors.append(f"evidence_status_not_valid:{manifest.get('status')}")
    return errors


def compute_stale_reasons(
    state: dict[str, Any],
    manifest: dict[str, Any],
    evidence_policy: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    baseline = state.get("current_baseline", {})
    provenance = manifest.get("provenance", {})
    dependencies = evidence_policy.get("freshness_dependencies", {})
    if not isinstance(dependencies, dict):
        return ["evidence_policy_freshness_dependencies_malformed"]

    for provenance_key, baseline_key in dependencies.items():
        evidence_value = dotted_get(provenance, str(provenance_key))
        baseline_value = dotted_get(baseline, str(baseline_key))
        if evidence_value is None:
            continue
        if baseline_value is None:
            reasons.append(f"baseline_missing:{baseline_key}")
        elif evidence_value != baseline_value:
            reasons.append(
                f"dependency_changed:{provenance_key}:evidence={evidence_value!r}:current={baseline_value!r}"
            )
    return reasons


def load_evidence_records(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
) -> tuple[list[EvidenceRecord], list[str]]:
    records: list[EvidenceRecord] = []
    errors: list[str] = []
    refs = gate_state.get("evidence_manifests", [])
    if not isinstance(refs, list):
        return [], [f"{gate_id}:evidence_manifests_not_list"]
    for reference in refs:
        if not isinstance(reference, str) or not reference:
            errors.append(f"{gate_id}:evidence_manifest_reference_invalid")
            continue
        manifest_path = resolve_ref(bundle.state_path, reference)
        try:
            manifest = load_data(manifest_path)
        except GovernanceError as exc:
            errors.append(f"{gate_id}:evidence_manifest_unreadable:{reference}:{exc}")
            continue
        provenance_errors = validate_provenance(
            manifest, manifest_path, bundle.evidence_policy
        )
        stale_reasons = compute_stale_reasons(
            bundle.state, manifest, bundle.evidence_policy
        )
        manifest_policy_hash = dotted_get(manifest, "provenance.policy_hash")
        current_policy_hash = policy_bundle_hash(bundle)
        if (
            manifest_policy_hash is not None
            and manifest_policy_hash != current_policy_hash
            and not any(
                reason.startswith("dependency_changed:policy_hash:")
                for reason in stale_reasons
            )
        ):
            stale_reasons.append(
                "dependency_changed:policy_hash:"
                f"evidence={manifest_policy_hash!r}:current_policy_bundle={current_policy_hash!r}"
            )
        schema_errors = validate_schema(
            manifest,
            "evidence-manifest.schema.json",
            f"evidence:{manifest.get('evidence_id', reference)}",
        )
        records.append(
            EvidenceRecord(
                path=manifest_path,
                manifest=manifest,
                schema_errors=tuple(schema_errors),
                provenance_errors=tuple(provenance_errors),
                stale_reasons=tuple(stale_reasons),
            )
        )
    return records, errors


def compute_scope_digest(
    bundle: GovernanceBundle, gate_id: str, evidence_records: Iterable[EvidenceRecord]
) -> str:
    state = bundle.state
    gate_state = mapping_or_empty(mapping_or_empty(state.get("gates")).get(gate_id))
    evidence_scope: list[dict[str, Any]] = []
    for record in evidence_records:
        manifest = record.manifest
        if not manifest.get("promotion_eligible") or manifest.get("exploratory_only"):
            continue
        evidence_scope.append(
            {
                "evidence_id": manifest.get("evidence_id"),
                "artifact_type": manifest.get("artifact_type"),
                "artifact_digest": dotted_get(manifest, "artifact.sha256"),
                "provenance": manifest.get("provenance"),
            }
        )
    evidence_scope.sort(key=lambda item: str(item.get("evidence_id")))
    waiver_scope: list[dict[str, Any]] = []
    for reference in sorted(
        item
        for item in list_or_empty(gate_state.get("waiver_records"))
        if isinstance(item, str)
    ):
        if not isinstance(reference, str):
            waiver_scope.append({"reference": repr(reference), "digest": None})
            continue
        try:
            waiver = load_data(resolve_ref(bundle.state_path, reference))
            digest = canonical_digest(waiver)
        except GovernanceError:
            digest = None
        waiver_scope.append({"reference": reference, "digest": digest})
    decision_records, _ = load_state_records(
        bundle, "decision_records", "decision-record.schema.json", "decision_id"
    )
    change_records, _ = load_state_records(
        bundle, "change_records", "change-record.schema.json", "change_id"
    )
    scoped_decisions = [
        record
        for record in decision_records
        if record.get("gate_id") == gate_id
        and record.get("candidate_id") == gate_state.get("candidate_id")
    ]
    scoped_changes = []
    for record in change_records:
        if gate_id not in string_set(record.get("affected_gates")):
            continue
        affected_candidates = string_set(record.get("affected_candidates"))
        if affected_candidates and gate_state.get("candidate_id") not in affected_candidates:
            continue
        scoped_changes.append(record)
    payload = {
        "schema_version": state.get("schema_version"),
        "project_id": state.get("project_id"),
        "gate_id": gate_id,
        "candidate_id": gate_state.get("candidate_id"),
        "candidate_authors": gate_state.get("candidate_authors", []),
        "baseline": state.get("current_baseline"),
        "policy_bundle_hash": policy_bundle_hash(bundle),
        "requirements_digest": canonical_digest(bundle.requirements),
        "risk_register_digest": canonical_digest(bundle.risk_register),
        "trusted_signers_digest": canonical_digest(bundle.trusted_signers),
        "decision_record_digests": sorted(
            canonical_digest(record) for record in scoped_decisions
        ),
        "change_record_digests": sorted(
            canonical_digest(record) for record in scoped_changes
        ),
        "evidence": evidence_scope,
        "waivers": waiver_scope,
    }
    return canonical_digest(payload)


def signature_payload(
    record: dict[str, Any], actor: dict[str, Any], record_type: str
) -> bytes:
    """Return the canonical bytes a human-controlled Ed25519 key must sign."""

    actor_payload = {key: value for key, value in actor.items() if key != "verification"}
    if record_type == "gate_review":
        body = {
            key: record.get(key)
            for key in (
                "schema_version",
                "review_id",
                "project_id",
                "gate_id",
                "candidate_id",
                "candidate_authors",
                "scope_digest",
                "status",
                "findings",
            )
        }
    elif record_type == "gate_approval":
        body = {
            key: record.get(key)
            for key in (
                "schema_version",
                "approval_id",
                "project_id",
                "gate_id",
                "candidate_id",
                "review_id",
                "review_digest",
                "scope_digest",
                "decision",
            )
        }
    elif record_type == "waiver":
        body = {
            key: record.get(key)
            for key in (
                "schema_version",
                "waiver_id",
                "project_id",
                "gate_id",
                "severity",
                "status",
                "scope",
                "baseline_digest",
                "owner",
                "rationale",
                "compensating_controls",
                "expires_at",
                "revalidation_triggers",
            )
        }
    elif record_type == "change_record":
        body = {
            key: record.get(key)
            for key in (
                "schema_version",
                "change_id",
                "project_id",
                "change_class",
                "status",
                "owner",
                "affected_gates",
                "affected_candidates",
                "reason",
                "before_fingerprints",
                "after_fingerprints",
                "invalidated_evidence_ids",
                "required_revalidation",
                "verification_evidence_ids",
                "created_at",
            )
        }
    else:
        raise GovernanceError(f"unsupported signature record type: {record_type}")
    payload = {"record_type": record_type, "record": body, "actor": actor_payload}
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def verify_human_signature(
    record: dict[str, Any],
    actor: Any,
    record_type: str,
    trusted_signers: dict[str, Any],
) -> tuple[bool, str | None]:
    if Ed25519PublicKey is None:
        return False, "cryptography_dependency_unavailable"
    if not isinstance(actor, dict):
        return False, "signature_actor_missing"
    actor_id = actor.get("actor_id")
    role = actor.get("role")
    verification = actor.get("verification")
    if not isinstance(verification, dict):
        return False, "signature_record_missing"
    if verification.get("method") != "ed25519":
        return False, "signature_method_not_ed25519"
    key_id = verification.get("key_id")
    if not isinstance(key_id, str) or not key_id:
        return False, "signature_key_id_missing"
    if key_id != actor_id:
        return False, "signature_key_id_actor_mismatch"

    registry = trusted_signers.get("signers", {})
    signer = registry.get(key_id) if isinstance(registry, dict) else None
    if not isinstance(signer, dict):
        return False, "signer_not_in_trusted_registry"
    if signer.get("enabled") is not True:
        return False, "trusted_signer_disabled"
    if signer.get("actor_type") != "human":
        return False, "trusted_signer_not_human"
    if signer.get("method") != "ed25519":
        return False, "trusted_signer_method_mismatch"
    if role not in string_set(signer.get("roles")):
        return False, "trusted_signer_role_mismatch"

    try:
        public_bytes = base64.b64decode(signer.get("public_key_base64", ""), validate=True)
        signature_bytes = base64.b64decode(
            verification.get("signature_base64", ""), validate=True
        )
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        public_key.verify(signature_bytes, signature_payload(record, actor, record_type))
    except (ValueError, TypeError, InvalidSignature) as exc:
        return False, f"signature_verification_failed:{type(exc).__name__}"
    return True, None


def validate_waiver(
    waiver: dict[str, Any],
    *,
    project_id: str,
    gate_id: str,
    candidate_id: str,
    baseline_digest: str,
    gate_policy: dict[str, Any],
    authorization_policy: dict[str, Any],
    trusted_signers: dict[str, Any],
    now: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    now = now or datetime.now(timezone.utc)
    waiver_id = waiver.get("waiver_id", "unknown")
    prefix = f"waiver:{waiver_id}"
    if waiver.get("project_id") != project_id:
        errors.append(f"{prefix}:project_id_mismatch")
    if waiver.get("gate_id") != gate_id:
        errors.append(f"{prefix}:gate_id_mismatch")
    if waiver.get("status") != "active":
        errors.append(f"{prefix}:status_not_active:{waiver.get('status')}")
    if waiver.get("baseline_digest") != baseline_digest:
        errors.append(f"{prefix}:baseline_scope_mismatch")
    severity = waiver.get("severity")
    non_waivable = string_set(
        mapping_or_empty(gate_policy.get("finding_policy")).get(
            "non_waivable_severities"
        )
    )
    if severity in non_waivable:
        errors.append(f"{prefix}:severity_not_waivable:{severity}")

    scope = waiver.get("scope")
    if not isinstance(scope, dict):
        errors.append(f"{prefix}:scope_missing")
    else:
        if scope.get("candidate_id") != candidate_id:
            errors.append(f"{prefix}:candidate_scope_mismatch")
        if not isinstance(scope.get("criterion_ids"), list) or not scope.get("criterion_ids"):
            errors.append(f"{prefix}:criterion_scope_missing")

    owner = waiver.get("owner")
    if (
        not isinstance(owner, dict)
        or owner.get("actor_type") != "human"
        or not owner.get("actor_id")
    ):
        errors.append(f"{prefix}:human_owner_missing")

    expiry = parse_utc(waiver.get("expires_at"))
    if expiry is None:
        errors.append(f"{prefix}:expiry_invalid")
    elif expiry <= now:
        errors.append(f"{prefix}:expired")

    if not waiver.get("rationale"):
        errors.append(f"{prefix}:rationale_missing")
    if not isinstance(waiver.get("compensating_controls"), list) or not waiver.get(
        "compensating_controls"
    ):
        errors.append(f"{prefix}:compensating_controls_missing")

    auth = mapping_or_empty(authorization_policy.get("waiver"))
    approvals = waiver.get("approvals")
    minimum = int(auth.get("minimum_human_approvals", 1))
    valid_approvals = 0
    if not isinstance(approvals, list):
        errors.append(f"{prefix}:approvals_missing")
        approvals = []
    for index, approval in enumerate(approvals):
        label = f"{prefix}:approval:{index}"
        if not isinstance(approval, dict):
            errors.append(f"{label}:not_mapping")
            continue
        if approval.get("actor_type") != auth.get("required_actor_type", "human"):
            errors.append(f"{label}:nonhuman_actor")
            continue
        if approval.get("role") not in string_set(auth.get("allowed_roles")):
            errors.append(f"{label}:role_not_authorized")
            continue
        if not approval.get("actor_id") or parse_utc(approval.get("signed_at")) is None:
            errors.append(f"{label}:identity_or_timestamp_invalid")
            continue
        if auth.get("require_distinct_from_owner", True) and isinstance(owner, dict):
            if approval.get("actor_id") == owner.get("actor_id"):
                errors.append(f"{label}:approver_is_waiver_owner")
                continue
        if auth.get("require_verified_signature", True):
            signature_valid, signature_error = verify_human_signature(
                waiver, approval, "waiver", trusted_signers
            )
            if not signature_valid:
                errors.append(f"{label}:{signature_error}")
                continue
        valid_approvals += 1
    if valid_approvals < minimum:
        errors.append(f"{prefix}:insufficient_human_approvals:{valid_approvals}/{minimum}")
    return errors


def load_valid_waivers(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    waivers: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for reference in list_or_empty(gate_state.get("waiver_records")):
        waiver_path = resolve_ref(bundle.state_path, str(reference))
        try:
            waiver = load_data(waiver_path)
        except GovernanceError as exc:
            errors.append(f"{gate_id}:waiver_unreadable:{reference}:{exc}")
            continue
        waiver_schema_errors = validate_schema(
            waiver,
            "waiver.schema.json",
            f"{gate_id}:waiver:{waiver.get('waiver_id', reference)}",
        )
        errors.extend(waiver_schema_errors)
        waiver_errors = validate_waiver(
            waiver,
            project_id=str(bundle.state.get("project_id")),
            gate_id=gate_id,
            candidate_id=str(gate_state.get("candidate_id")),
            baseline_digest=canonical_digest(bundle.state.get("current_baseline", {})),
            gate_policy=bundle.gate_policy,
            authorization_policy=bundle.authorization_policy,
            trusted_signers=bundle.trusted_signers,
        )
        if waiver_schema_errors or waiver_errors:
            errors.extend(waiver_errors)
        elif waiver.get("waiver_id"):
            waivers[str(waiver["waiver_id"])] = waiver
    return waivers, errors


def validate_review(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
    scope_digest: str,
    valid_waivers: dict[str, dict[str, Any]],
) -> tuple[bool, list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []
    reference = gate_state.get("review_record")
    if not reference:
        return False, [f"{gate_id}:independent_review_missing"], warnings, None
    review_path = resolve_ref(bundle.state_path, str(reference))
    try:
        review = load_data(review_path)
    except GovernanceError as exc:
        return False, [f"{gate_id}:review_unreadable:{exc}"], warnings, None

    errors.extend(
        validate_schema(
            review,
            "gate-review.schema.json",
            f"{gate_id}:review:{review.get('review_id', reference)}",
        )
    )

    review_id = review.get("review_id")
    expected = {
        "project_id": bundle.state.get("project_id"),
        "gate_id": gate_id,
        "candidate_id": gate_state.get("candidate_id"),
        "scope_digest": scope_digest,
        "status": "completed",
    }
    for key, value in expected.items():
        if review.get(key) != value:
            errors.append(f"{gate_id}:review_{key}_mismatch")
    review_authors = sorted(string_set(review.get("candidate_authors")))
    state_authors = sorted(string_set(gate_state.get("candidate_authors")))
    if review_authors != state_authors:
        errors.append(f"{gate_id}:review_candidate_authors_mismatch")

    reviewer = review.get("reviewer")
    auth = mapping_or_empty(bundle.authorization_policy.get("review"))
    if not isinstance(reviewer, dict):
        errors.append(f"{gate_id}:reviewer_missing")
    else:
        reviewer_id = reviewer.get("actor_id")
        if reviewer.get("actor_type") != auth.get("required_actor_type", "human"):
            errors.append(f"{gate_id}:reviewer_not_human")
        if reviewer.get("role") not in string_set(auth.get("allowed_roles")):
            errors.append(f"{gate_id}:reviewer_role_not_authorized")
        gate_definition = mapping_or_empty(
            mapping_or_empty(bundle.gate_policy.get("gates")).get(gate_id)
        )
        gate_roles = string_set(gate_definition.get("required_review_roles"))
        if reviewer.get("role") not in gate_roles:
            errors.append(f"{gate_id}:reviewer_role_not_valid_for_gate")
        if auth.get("require_independence", True):
            if reviewer.get("independent") is not True:
                errors.append(f"{gate_id}:reviewer_not_marked_independent")
            if reviewer_id in string_set(gate_state.get("candidate_authors")):
                errors.append(f"{gate_id}:reviewer_is_candidate_author")
        if not reviewer_id or parse_utc(reviewer.get("signed_at")) is None:
            errors.append(f"{gate_id}:reviewer_identity_or_timestamp_invalid")
        if auth.get("require_verified_signature", True):
            signature_valid, signature_error = verify_human_signature(
                review, reviewer, "gate_review", bundle.trusted_signers
            )
            if not signature_valid:
                errors.append(f"{gate_id}:review_{signature_error}")

    for finding in list_or_empty(review.get("findings")):
        if not isinstance(finding, dict):
            errors.append(f"{gate_id}:review_finding_not_mapping")
            continue
        severity = finding.get("severity")
        status = finding.get("status")
        finding_id = finding.get("finding_id", "unknown")
        if severity in {"BLOCKER", "MAJOR"} and status == "open":
            errors.append(f"{gate_id}:open_{severity}:{finding_id}")
        elif status == "waived":
            waiver_id = finding.get("waiver_id")
            if not waiver_id or waiver_id not in valid_waivers:
                errors.append(f"{gate_id}:finding_has_invalid_waiver:{finding_id}")
            elif finding_id not in string_set(
                mapping_or_empty(valid_waivers[waiver_id].get("scope")).get(
                    "criterion_ids"
                )
            ):
                errors.append(f"{gate_id}:finding_outside_waiver_scope:{finding_id}")
        elif severity == "MINOR" and status == "open":
            warnings.append(f"{gate_id}:open_MINOR:{finding_id}")

    return not errors, errors, warnings, str(review_id) if review_id else None


def blocking_risk_errors(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
    valid_waivers: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    risks = bundle.risk_register.get("risks", [])
    if not isinstance(risks, list):
        return ["risk_register_risks_not_list"], warnings
    candidate_id = gate_state.get("candidate_id")
    for risk in risks:
        if not isinstance(risk, dict):
            errors.append("risk_record_not_mapping")
            continue
        affected_gates = string_set(risk.get("affected_gates"))
        affected_candidates = string_set(risk.get("affected_candidates"))
        if gate_id not in affected_gates:
            continue
        if affected_candidates and candidate_id not in affected_candidates:
            continue
        severity = risk.get("severity")
        status = risk.get("status")
        risk_id = risk.get("risk_id", "unknown")
        if severity in {"BLOCKER", "MAJOR"} and status == "open":
            errors.append(f"{gate_id}:open_{severity}_risk:{risk_id}")
        elif status == "waived":
            waiver_id = risk.get("waiver_id")
            if not waiver_id or waiver_id not in valid_waivers:
                errors.append(f"{gate_id}:risk_has_invalid_waiver:{risk_id}")
            elif risk_id not in string_set(
                mapping_or_empty(valid_waivers[waiver_id].get("scope")).get(
                    "criterion_ids"
                )
            ):
                errors.append(f"{gate_id}:risk_outside_waiver_scope:{risk_id}")
        elif severity == "MINOR" and status == "open":
            warnings.append(f"{gate_id}:open_MINOR_risk:{risk_id}")
    return errors, warnings


def change_control_errors(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
) -> list[str]:
    """Block promotion while an applicable ECO/change record remains open."""

    records, errors = load_state_records(
        bundle, "change_records", "change-record.schema.json", "change_id"
    )
    candidate_id = gate_state.get("candidate_id")
    for record in records:
        change_id = record.get("change_id", "unknown")
        if record.get("project_id") != bundle.state.get("project_id"):
            errors.append(f"{gate_id}:change:{change_id}:project_id_mismatch")
            continue
        if gate_id not in string_set(record.get("affected_gates")):
            continue
        affected_candidates = string_set(record.get("affected_candidates"))
        if affected_candidates and candidate_id not in affected_candidates:
            continue
        if record.get("status") not in {"closed", "cancelled"}:
            errors.append(
                f"{gate_id}:open_change_control:{change_id}:{record.get('status')}"
            )
            continue
        closer = record.get("closed_by")
        change_auth = mapping_or_empty(bundle.authorization_policy.get("change"))
        if not isinstance(closer, dict):
            errors.append(f"{gate_id}:change:{change_id}:human_closure_missing")
            continue
        if closer.get("actor_type") != change_auth.get("required_actor_type", "human"):
            errors.append(f"{gate_id}:change:{change_id}:closure_actor_not_human")
        if closer.get("role") not in string_set(change_auth.get("allowed_roles")):
            errors.append(f"{gate_id}:change:{change_id}:closure_role_not_authorized")
        if not closer.get("actor_id") or parse_utc(closer.get("closed_at")) is None:
            errors.append(f"{gate_id}:change:{change_id}:closure_identity_or_time_invalid")
        signature_valid, signature_error = verify_human_signature(
            record, closer, "change_record", bundle.trusted_signers
        )
        if not signature_valid:
            errors.append(
                f"{gate_id}:change:{change_id}:closure_{signature_error}"
            )
    return errors


def _compare_numeric(value: float, operator: str, expected: Any) -> bool:
    if not math.isfinite(value):
        return False
    if operator == "between":
        if not isinstance(expected, list) or len(expected) != 2:
            return False
        low, high = float(expected[0]), float(expected[1])
        return low <= value <= high
    target = float(expected)
    return {
        ">=": value >= target,
        ">": value > target,
        "<=": value <= target,
        "<": value < target,
        "==": value == target,
    }.get(operator, False)


def evaluate_controlling_metrics(
    bundle: GovernanceBundle,
    gate_id: str,
    valid_records: Iterable[EvidenceRecord],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    metric_policy = mapping_or_empty(bundle.evidence_policy.get("metric_policy"))
    controlling = metric_policy.get("controlling_classification", "controlling")
    requirements = bundle.requirements.get("requirements", [])
    if not isinstance(requirements, list):
        return ["requirements_entries_not_list"], notes

    results_by_requirement: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for record in valid_records:
        artifact_type = str(record.manifest.get("artifact_type", ""))
        for result in list_or_empty(record.manifest.get("metrics")):
            if isinstance(result, dict) and result.get("requirement_id"):
                results_by_requirement.setdefault(str(result["requirement_id"]), []).append(
                    (artifact_type, result)
                )

    applicable_count = 0
    for requirement in requirements:
        if not isinstance(requirement, dict):
            errors.append("requirement_record_not_mapping")
            continue
        if requirement.get("classification") != controlling:
            continue
        if requirement.get("status") != "active":
            continue
        if gate_id not in string_set(requirement.get("applies_to_gates")):
            continue
        applicable_count += 1
        requirement_id = str(requirement.get("requirement_id", "unknown"))
        allowed_artifact_types = string_set(requirement.get("evidence_artifact_types"))
        results = [
            result
            for artifact_type, result in results_by_requirement.get(requirement_id, [])
            if artifact_type in allowed_artifact_types
        ]
        if not results:
            errors.append(f"{gate_id}:controlling_metric_missing:{requirement_id}")
            continue
        evaluations: list[bool] = []
        failed_values: list[Any] = []
        for result in results:
            if result.get("metric") != requirement.get("metric"):
                errors.append(f"{gate_id}:metric_name_mismatch:{requirement_id}")
                evaluations.append(False)
                continue
            if metric_policy.get("require_exact_unit_match", True) and result.get(
                "unit"
            ) != requirement.get("unit"):
                errors.append(f"{gate_id}:metric_unit_mismatch:{requirement_id}")
                evaluations.append(False)
                continue
            try:
                value = float(result.get("value"))
                passed = _compare_numeric(
                    value,
                    str(requirement.get("operator")),
                    requirement.get("value"),
                )
            except (TypeError, ValueError):
                passed = False
            evaluations.append(passed)
            if not passed:
                failed_values.append(result.get("value"))
        aggregation = requirement.get(
            "aggregation", metric_policy.get("default_aggregation", "all")
        )
        satisfied = (
            aggregation == "all" and evaluations and all(evaluations)
        ) or (aggregation == "any" and any(evaluations))
        if satisfied:
            notes.append(f"{gate_id}:controlling_metric_satisfied:{requirement_id}")
        else:
            errors.append(
                f"{gate_id}:controlling_metric_failed:{requirement_id}:"
                f"values={failed_values!r}:aggregation={aggregation}"
            )
    gate_definition = mapping_or_empty(
        mapping_or_empty(bundle.gate_policy.get("gates")).get(gate_id)
    )
    if gate_definition.get("requires_metric_evaluation") is True and applicable_count == 0:
        errors.append(f"{gate_id}:controlling_requirement_not_configured")
    return errors, notes


def validate_approval(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
    scope_digest: str,
    review_id: str | None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    reference = gate_state.get("approval_record")
    if not reference:
        return False, [f"{gate_id}:human_approval_record_missing"]
    approval_path = resolve_ref(bundle.state_path, str(reference))
    try:
        approval = load_data(approval_path)
    except GovernanceError as exc:
        return False, [f"{gate_id}:approval_unreadable:{exc}"]

    errors.extend(
        validate_schema(
            approval,
            "approval-record.schema.json",
            f"{gate_id}:approval:{approval.get('approval_id', reference)}",
        )
    )

    review_digest = None
    review_reference = gate_state.get("review_record")
    if review_reference:
        try:
            review_digest = canonical_digest(
                load_data(resolve_ref(bundle.state_path, str(review_reference)))
            )
        except GovernanceError as exc:
            errors.append(f"{gate_id}:approval_bound_review_unreadable:{exc}")

    expected = {
        "project_id": bundle.state.get("project_id"),
        "gate_id": gate_id,
        "candidate_id": gate_state.get("candidate_id"),
        "scope_digest": scope_digest,
        "decision": "approved",
        "review_id": review_id,
        "review_digest": review_digest,
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            errors.append(f"{gate_id}:approval_{key}_mismatch")

    approver = approval.get("approver")
    auth = mapping_or_empty(bundle.authorization_policy.get("approval"))
    if not isinstance(approver, dict):
        errors.append(f"{gate_id}:approver_missing")
    else:
        approver_id = approver.get("actor_id")
        if approver.get("actor_type") != auth.get("required_actor_type", "human"):
            errors.append(f"{gate_id}:approval_actor_not_human")
        if approver.get("role") not in string_set(auth.get("allowed_roles")):
            errors.append(f"{gate_id}:approver_role_not_authorized")
        gate_definition = mapping_or_empty(
            mapping_or_empty(bundle.gate_policy.get("gates")).get(gate_id)
        )
        gate_roles = string_set(gate_definition.get("required_approval_roles"))
        if approver.get("role") not in gate_roles:
            errors.append(f"{gate_id}:approver_role_not_valid_for_gate")
        if not approver_id or parse_utc(approver.get("signed_at")) is None:
            errors.append(f"{gate_id}:approver_identity_or_timestamp_invalid")
        if auth.get("require_verified_signature", True):
            signature_valid, signature_error = verify_human_signature(
                approval, approver, "gate_approval", bundle.trusted_signers
            )
            if not signature_valid:
                errors.append(f"{gate_id}:approval_{signature_error}")
        if auth.get("require_distinct_from_candidate_authors", True) and approver_id in string_set(
            gate_state.get("candidate_authors")
        ):
            errors.append(f"{gate_id}:approver_is_candidate_author")
        status_actor = gate_state.get("status_actor", {})
        if not isinstance(status_actor, dict) or status_actor.get("actor_id") != approver_id:
            errors.append(f"{gate_id}:approved_status_actor_mismatch")
        if auth.get("require_distinct_from_reviewer", True) and review_reference:
            try:
                bound_review = load_data(
                    resolve_ref(bundle.state_path, str(review_reference))
                )
                reviewer_id = dotted_get(bound_review, "reviewer.actor_id")
                if approver_id == reviewer_id:
                    errors.append(f"{gate_id}:approver_is_independent_reviewer")
            except GovernanceError:
                # The unreadable review is already reported above and cannot
                # result in an effective approval.
                pass
    return not errors, errors


def manifest_identity_errors(
    bundle: GovernanceBundle,
    gate_id: str,
    gate_state: dict[str, Any],
    record: EvidenceRecord,
) -> list[str]:
    manifest = record.manifest
    errors: list[str] = []
    expected = {
        "project_id": bundle.state.get("project_id"),
        "candidate_id": gate_state.get("candidate_id"),
        "gate_id": gate_id,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"evidence_{key}_mismatch:{manifest.get('evidence_id')}")
    return errors
