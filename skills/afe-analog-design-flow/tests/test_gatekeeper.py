from __future__ import annotations

import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
POLICIES = SKILL_ROOT / "governance" / "policies"
sys.path.insert(0, str(SCRIPTS))

from gatekeeper import evaluate_project  # noqa: E402
from provenance_check import check_provenance  # noqa: E402
from stale_evidence_check import check_staleness  # noqa: E402
from governance_common import (  # noqa: E402
    canonical_digest,
    compute_scope_digest,
    dotted_get,
    governance_contract_hash,
    load_bundle,
    load_data,
    load_evidence_records,
    sha256_file,
    signature_payload,
)


def digest(label: str) -> str:
    return f"sha256:{hashlib.sha256(label.encode('utf-8')).hexdigest()}"


def set_dotted(target: dict, dotted: str, value) -> None:
    current = target
    parts = dotted.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = copy.deepcopy(value)


def directory_digest(root: Path) -> str:
    hasher = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        hasher.update(path.relative_to(root).as_posix().encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


class ProjectFixture:
    def __init__(self, root: Path, active_gate: str = "G0") -> None:
        self.root = root
        self.state_path = root / "project-state.json"
        self.private_keys = {
            "reviewer-1": Ed25519PrivateKey.generate(),
            "approver-1": Ed25519PrivateKey.generate(),
            "waiver-1": Ed25519PrivateKey.generate(),
        }
        self.gate_policy_path = (POLICIES / "default-gates.yaml").resolve()
        self.evidence_policy_path = (POLICIES / "default-evidence.yaml").resolve()
        self.authorization_policy_path = (
            POLICIES / "default-authorization.yaml"
        ).resolve()
        self.gate_policy = load_data(self.gate_policy_path)
        self.evidence_policy = load_data(self.evidence_policy_path)
        self.authorization_policy = load_data(self.authorization_policy_path)
        self.gate_order = list(self.gate_policy["gate_order"])
        self.active_gate = active_gate
        self.active_index = self.gate_order.index(active_gate)
        self.manifest_paths: dict[tuple[str, str], Path] = {}

        policy_hash = governance_contract_hash(
            self.gate_policy,
            self.evidence_policy,
            self.authorization_policy,
        )
        self.baseline = {
            "source_commit": "a" * 40,
            "spec_hash": digest("spec-v1"),
            "netlist_hash": digest("netlist-v1"),
            "testbench_hash": digest("testbench-v1"),
            "command_profile_hash": digest("command-v1"),
            "metric_extractor_hash": digest("extractor-v1"),
            "policy_hash": policy_hash,
            "layout_hash": digest("layout-v1"),
            "pex_hash": digest("pex-v1"),
            "extraction_deck_hash": digest("extract-deck-v1"),
            "pdk": {
                "id": "TEST_PDK",
                "release": "R1",
                "model_hash": digest("pdk-model-v1"),
                "model_sections": ["tt", "mc"],
            },
            "simulator": {
                "name": "spectre",
                "version": "test-1",
                "executable_hash": digest("spectre-bin-v1"),
            },
        }

        self._write_support_files()
        self.state = self._initial_state()
        self._create_evidence_through_active_gate()
        self.save_state()
        self._create_reviews_and_predecessor_approvals()
        self.save_state()

    def _write_json(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _public_key_b64(self, actor_id: str) -> str:
        raw = self.private_keys[actor_id].public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    def _write_support_files(self) -> None:
        requirements = {
            "schema_version": "1.0.0",
            "project_id": "AFE-TEST",
            "spec_hash": self.baseline["spec_hash"],
            "requirements": [
                {
                    "requirement_id": "REQ-BEHAVIORAL-MARGIN",
                    "description": "Behavioral chain budget margin",
                    "classification": "controlling",
                    "status": "active",
                    "owner": {"actor_type": "human", "actor_id": "spec-owner"},
                    "applies_to_gates": ["G4"],
                    "metric": "budget_margin_db",
                    "operator": ">=",
                    "value": 0.0,
                    "unit": "dB",
                    "aggregation": "all",
                    "evidence_artifact_types": ["chain_budget_model"],
                },
                {
                    "requirement_id": "REQ-BLOCK-GAIN",
                    "description": "Allocated block gain",
                    "classification": "controlling",
                    "status": "active",
                    "owner": {"actor_type": "human", "actor_id": "spec-owner"},
                    "applies_to_gates": ["G5"],
                    "metric": "block_gain_db",
                    "operator": ">=",
                    "value": 20.0,
                    "unit": "dB",
                    "aggregation": "all",
                    "evidence_artifact_types": ["module_report"],
                },
                {
                    "requirement_id": "REQ-GAIN",
                    "description": "Worst-case gain",
                    "classification": "controlling",
                    "status": "active",
                    "owner": {"actor_type": "human", "actor_id": "spec-owner"},
                    "applies_to_gates": ["G6", "G9"],
                    "metric": "gain_db",
                    "operator": ">=",
                    "value": 40.0,
                    "unit": "dB",
                    "aggregation": "all",
                    "evidence_artifact_types": [
                        "metric_results",
                        "post_layout_pvt_evidence",
                    ],
                }
            ],
        }
        risk_register = {
            "schema_version": "1.0.0",
            "project_id": "AFE-TEST",
            "register_revision": 0,
            "risks": [],
        }
        trusted_signers = {
            "schema_version": "1.0.0",
            "project_id": "AFE-TEST",
            "signers": {
                "reviewer-1": {
                    "actor_type": "human",
                    "roles": [
                        "independent_reviewer",
                        "signoff_reviewer",
                        "gate_approver",
                    ],
                    "method": "ed25519",
                    "public_key_base64": self._public_key_b64("reviewer-1"),
                    "enabled": True,
                },
                "approver-1": {
                    "actor_type": "human",
                    "roles": ["gate_approver", "design_authority", "release_authority"],
                    "method": "ed25519",
                    "public_key_base64": self._public_key_b64("approver-1"),
                    "enabled": True,
                },
                "waiver-1": {
                    "actor_type": "human",
                    "roles": ["waiver_approver", "design_authority"],
                    "method": "ed25519",
                    "public_key_base64": self._public_key_b64("waiver-1"),
                    "enabled": True,
                },
            },
        }
        self._write_json(self.root / "requirements.json", requirements)
        self._write_json(self.root / "risks.json", risk_register)
        self._write_json(self.root / "trusted-signers.json", trusted_signers)

    def _initial_state(self) -> dict:
        gates = {}
        for index, gate_id in enumerate(self.gate_order):
            if index < self.active_index:
                status = "approved"
                actor = {
                    "actor_type": "human",
                    "actor_id": "approver-1",
                    "updated_at": "2030-01-01T00:00:00Z",
                }
            elif index == self.active_index:
                status = "human_approval_required"
                actor = {
                    "actor_type": "codex",
                    "actor_id": "codex-test",
                    "updated_at": "2030-01-01T00:00:00Z",
                }
            else:
                status = "not_started"
                actor = {
                    "actor_type": "system",
                    "actor_id": "state-initializer",
                    "updated_at": "2030-01-01T00:00:00Z",
                }
            gates[gate_id] = {
                "status": status,
                "status_actor": actor,
                "candidate_id": f"AFE-TEST-{gate_id}-R1" if index <= self.active_index else None,
                "candidate_authors": ["designer-1"] if index <= self.active_index else [],
                "evidence_manifests": [],
                "waiver_records": [],
                "review_record": None,
                "approval_record": None,
            }
        return {
            "schema_version": "1.0.0",
            "project_id": "AFE-TEST",
            "state_revision": 1,
            "template_only": False,
            "current_baseline": copy.deepcopy(self.baseline),
            "policies": {
                "gate_policy": str(self.gate_policy_path),
                "evidence_policy": str(self.evidence_policy_path),
                "authorization_policy": str(self.authorization_policy_path),
            },
            "requirements_traceability": "requirements.json",
            "risk_register": "risks.json",
            "trusted_signers": "trusted-signers.json",
            "decision_records": [],
            "change_records": [],
            "gates": gates,
        }

    def save_state(self) -> None:
        self._write_json(self.state_path, self.state)

    def _evidence_level(self, gate_id: str, artifact_type: str) -> str:
        number = int(gate_id[1:])
        if number <= 2:
            return "analysis"
        if number == 3:
            return "primitive"
        if number == 4:
            return "behavioral"
        if number == 5:
            return "transistor_schematic"
        if number == 6:
            return "monte_carlo" if artifact_type == "monte_carlo_evidence" else "transistor_schematic"
        if number == 7:
            return "layout_planning"
        if number == 8:
            return "pex"
        if number == 9:
            return (
                "post_layout_monte_carlo"
                if artifact_type == "post_layout_monte_carlo_evidence"
                else "post_layout"
            )
        return "release"

    def _provenance(self, level: str) -> dict:
        full = {
            "source_commit": self.baseline["source_commit"],
            "evidence_commit": "e" * 40,
            "spec_hash": self.baseline["spec_hash"],
            "netlist_hash": self.baseline["netlist_hash"],
            "testbench_hash": self.baseline["testbench_hash"],
            "command_profile_hash": self.baseline["command_profile_hash"],
            "metric_extractor_hash": self.baseline["metric_extractor_hash"],
            "policy_hash": self.baseline["policy_hash"],
            "layout_hash": self.baseline["layout_hash"],
            "pex_hash": self.baseline["pex_hash"],
            "extraction_deck_hash": self.baseline["extraction_deck_hash"],
            "timestamp_utc": "2030-01-01T00:00:00Z",
            "command": "spectre -64 test.scs",
            "pdk": copy.deepcopy(self.baseline["pdk"]),
            "simulator": copy.deepcopy(self.baseline["simulator"]),
            "monte_carlo": {
                "seed": 12345,
                "sample_count": 200,
                "statistical_section": "mc",
            },
        }
        required = list(self.evidence_policy["required_provenance"]["all"])
        required.extend(self.evidence_policy["required_provenance"].get(level, []))
        result = {}
        for field in dict.fromkeys(required):
            set_dotted(result, field, dotted_get(full, field))
        return result

    def _create_manifest(self, gate_id: str, artifact_type: str) -> Path:
        artifact_path = self.root / "artifacts" / f"{gate_id}-{artifact_type}.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"{gate_id}:{artifact_type}\n", encoding="utf-8")
        manifest_path = self.root / "evidence" / f"{gate_id}-{artifact_type}.json"
        level = self._evidence_level(gate_id, artifact_type)
        metrics = []
        if (gate_id, artifact_type) == ("G4", "chain_budget_model"):
            metrics.append(
                {
                    "requirement_id": "REQ-BEHAVIORAL-MARGIN",
                    "metric": "budget_margin_db",
                    "value": 3.0,
                    "unit": "dB",
                    "condition": "worst_case",
                }
            )
        elif (gate_id, artifact_type) == ("G5", "module_report"):
            metrics.append(
                {
                    "requirement_id": "REQ-BLOCK-GAIN",
                    "metric": "block_gain_db",
                    "value": 25.0,
                    "unit": "dB",
                    "condition": "worst_case",
                }
            )
        elif (gate_id, artifact_type) in {
            ("G6", "metric_results"),
            ("G9", "post_layout_pvt_evidence"),
        }:
            metrics.append(
                {
                    "requirement_id": "REQ-GAIN",
                    "metric": "gain_db",
                    "value": 45.0,
                    "unit": "dB",
                    "condition": "worst_case",
                }
            )
        manifest = {
            "schema_version": "1.0.0",
            "object_kind": "analysis_result",
            "evidence_id": f"EV-{gate_id}-{artifact_type}",
            "project_id": "AFE-TEST",
            "candidate_id": f"AFE-TEST-{gate_id}-R1",
            "gate_id": gate_id,
            "artifact_type": artifact_type,
            "evidence_level": level,
            "promotion_eligible": True,
            "exploratory_only": False,
            "contains_functional_proxy": False,
            "proxy_kinds": [],
            "status": "valid",
            "artifact": {
                "path": Path("..", "artifacts", artifact_path.name).as_posix(),
                "sha256": sha256_file(artifact_path),
            },
            "provenance": self._provenance(level),
            "metrics": metrics,
        }
        self._write_json(manifest_path, manifest)
        self.manifest_paths[(gate_id, artifact_type)] = manifest_path
        return manifest_path

    def _create_evidence_through_active_gate(self) -> None:
        for gate_id in self.gate_order[: self.active_index + 1]:
            refs = []
            for artifact_type in self.gate_policy["gates"][gate_id]["mandatory_artifacts"]:
                refs.append(self._rel(self._create_manifest(gate_id, artifact_type)))
            self.state["gates"][gate_id]["evidence_manifests"] = refs

    def _sign_actor(self, record: dict, actor: dict, record_type: str) -> None:
        actor.pop("verification", None)
        signature = self.private_keys[actor["actor_id"]].sign(
            signature_payload(record, actor, record_type)
        )
        actor["verification"] = {
            "method": "ed25519",
            "key_id": actor["actor_id"],
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        }

    def _create_reviews_and_predecessor_approvals(self) -> None:
        for index, gate_id in enumerate(self.gate_order[: self.active_index + 1]):
            self.save_state()
            bundle = load_bundle(self.state_path)
            gate_state = bundle.state["gates"][gate_id]
            records, errors = load_evidence_records(bundle, gate_id, gate_state)
            if errors:
                raise AssertionError(errors)
            scope = compute_scope_digest(bundle, gate_id, records)
            review = {
                "schema_version": "1.0.0",
                "review_id": f"REV-{gate_id}",
                "project_id": "AFE-TEST",
                "gate_id": gate_id,
                "candidate_id": gate_state["candidate_id"],
                "candidate_authors": ["designer-1"],
                "scope_digest": scope,
                "status": "completed",
                "reviewer": {
                    "actor_type": "human",
                    "actor_id": "reviewer-1",
                    "role": (
                        "signoff_reviewer"
                        if int(gate_id[1:]) >= 9
                        else "independent_reviewer"
                    ),
                    "independent": True,
                    "signed_at": "2030-01-01T00:00:00Z",
                },
                "findings": [],
            }
            self._sign_actor(review, review["reviewer"], "gate_review")
            review_path = self.root / "reviews" / f"{gate_id}.json"
            self._write_json(review_path, review)
            self.state["gates"][gate_id]["review_record"] = self._rel(review_path)

            if index < self.active_index:
                self._create_approval(gate_id, scope, review["review_id"])

    def _create_approval(self, gate_id: str, scope: str, review_id: str) -> Path:
        review_path = resolve(
            self.root, self.state["gates"][gate_id]["review_record"]
        )
        approval = {
            "schema_version": "1.0.0",
            "approval_id": f"APR-{gate_id}",
            "project_id": "AFE-TEST",
            "gate_id": gate_id,
            "candidate_id": self.state["gates"][gate_id]["candidate_id"],
            "review_id": review_id,
            "review_digest": canonical_digest(self._read_json(review_path)),
            "scope_digest": scope,
            "decision": "approved",
            "approver": {
                "actor_type": "human",
                "actor_id": "approver-1",
                "role": "release_authority" if gate_id == "G10" else "gate_approver",
                "signed_at": "2030-01-01T00:00:00Z",
            },
        }
        self._sign_actor(approval, approval["approver"], "gate_approval")
        approval_path = self.root / "approvals" / f"{gate_id}.json"
        self._write_json(approval_path, approval)
        self.state["gates"][gate_id]["approval_record"] = self._rel(approval_path)
        self.state["gates"][gate_id]["status"] = "approved"
        self.state["gates"][gate_id]["status_actor"] = {
            "actor_type": "human",
            "actor_id": "approver-1",
            "updated_at": "2030-01-01T00:00:00Z",
        }
        return approval_path

    def approve_gate(self, gate_id: str) -> None:
        self.save_state()
        bundle = load_bundle(self.state_path)
        gate_state = bundle.state["gates"][gate_id]
        records, errors = load_evidence_records(bundle, gate_id, gate_state)
        if errors:
            raise AssertionError(errors)
        scope = compute_scope_digest(bundle, gate_id, records)
        review = self._read_json(resolve(self.root, gate_state["review_record"]))
        self._create_approval(gate_id, scope, review["review_id"])
        self.save_state()

    def resign_review(self, gate_id: str) -> None:
        path = resolve(self.root, self.state["gates"][gate_id]["review_record"])
        review = self._read_json(path)
        self._sign_actor(review, review["reviewer"], "gate_review")
        self._write_json(path, review)

    def manifest(self, gate_id: str, artifact_type: str) -> tuple[Path, dict]:
        path = self.manifest_paths[(gate_id, artifact_type)]
        return path, self._read_json(path)

    def save_manifest(self, path: Path, manifest: dict) -> None:
        self._write_json(path, manifest)

    def add_valid_waiver(self, gate_id: str, criterion_id: str) -> str:
        waiver_id = f"WVR-{gate_id}-{criterion_id}"
        waiver = {
            "schema_version": "1.0.0",
            "waiver_id": waiver_id,
            "project_id": "AFE-TEST",
            "gate_id": gate_id,
            "severity": "MAJOR",
            "status": "active",
            "scope": {
                "candidate_id": self.state["gates"][gate_id]["candidate_id"],
                "criterion_ids": [criterion_id],
                "evidence_ids": [],
            },
            "baseline_digest": canonical_digest(self.state["current_baseline"]),
            "owner": {"actor_type": "human", "actor_id": "risk-owner"},
            "rationale": "Bounded test waiver",
            "compensating_controls": ["Independent follow-up before G9"],
            "expires_at": "2099-01-01T00:00:00Z",
            "revalidation_triggers": ["candidate_or_baseline_change"],
            "approvals": [
                {
                    "actor_type": "human",
                    "actor_id": "waiver-1",
                    "role": "waiver_approver",
                    "signed_at": "2030-01-01T00:00:00Z",
                }
            ],
        }
        self._sign_actor(waiver, waiver["approvals"][0], "waiver")
        path = self.root / "waivers" / f"{waiver_id}.json"
        self._write_json(path, waiver)
        self.state["gates"][gate_id]["waiver_records"].append(self._rel(path))
        self.save_state()
        return waiver_id

    def report(self) -> dict:
        self.save_state()
        return evaluate_project(load_bundle(self.state_path))


def resolve(root: Path, reference: str) -> Path:
    path = Path(reference)
    return path if path.is_absolute() else root / path


class GatekeeperAcceptanceTests(unittest.TestCase):
    def fixture(self, active_gate: str) -> ProjectFixture:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return ProjectFixture(Path(temp.name), active_gate)

    def assert_error_contains(self, gate: dict, fragment: str) -> None:
        self.assertTrue(
            any(fragment in error for error in gate["errors"]),
            f"missing error fragment {fragment!r}: {gate['errors']}",
        )

    def test_missing_human_approval_keeps_next_gate_not_started(self) -> None:
        fx = self.fixture("G0")
        report = fx.report()
        self.assertFalse(report["gates"]["G0"]["effective_approved"])
        self.assertEqual(report["gates"]["G1"]["current_status"], "not_started")
        self.assertEqual(report["gates"]["G1"]["suggested_status"], "not_started")

    def test_next_gate_cannot_start_without_predecessor_human_approval(self) -> None:
        fx = self.fixture("G0")
        fx.state["gates"]["G1"].update(
            {
                "status": "in_progress",
                "candidate_id": "AFE-TEST-G1-R1",
                "candidate_authors": ["designer-1"],
                "status_actor": {
                    "actor_type": "codex",
                    "actor_id": "codex-test",
                    "updated_at": "2030-01-01T00:00:00Z",
                },
            }
        )
        gate = fx.report()["gates"]["G1"]
        self.assert_error_contains(gate, "predecessor_not_human_approved")
        self.assertEqual(gate["suggested_status"], "not_started")

    def test_approval_actor_codex_is_rejected(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        approval_path = resolve(fx.root, fx.state["gates"]["G0"]["approval_record"])
        approval = fx._read_json(approval_path)
        approval["approver"]["actor_type"] = "codex"
        fx._write_json(approval_path, approval)
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "approval_actor_not_human")
        self.assertFalse(gate["effective_approved"])

    def test_automation_cannot_write_approved_state(self) -> None:
        fx = self.fixture("G0")
        fx.state["gates"]["G0"]["status"] = "approved"
        fx.state["gates"]["G0"]["approval_record"] = None
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "automation_actor_forbidden_state")
        self.assert_error_contains(gate, "human_only_state_has_nonhuman_actor")

    def test_filename_exists_but_controlling_metric_fails(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "metric_results")
        manifest["metrics"][0]["value"] = 20.0
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "controlling_metric_failed:REQ-GAIN")
        self.assertFalse(gate["eligible_for_human_close"])

    def test_source_commit_mismatch_marks_evidence_stale(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "metric_results")
        manifest["provenance"]["source_commit"] = "b" * 40
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assertIn(manifest["evidence_id"], gate["stale_evidence_ids"])
        self.assertEqual(gate["suggested_status"], "stale")

    def test_spec_hash_change_invalidates_dependent_approvals(self) -> None:
        fx = self.fixture("G1")
        fx.state["current_baseline"]["spec_hash"] = digest("spec-v2")
        report = fx.report()
        self.assertIn("requirements_spec_hash_stale", report["global_errors"])
        self.assertFalse(report["gates"]["G0"]["effective_approved"])
        self.assertEqual(report["gates"]["G1"]["suggested_status"], "not_started")

    def test_netlist_or_testbench_change_invalidates_old_simulation(self) -> None:
        for key in ("netlist_hash", "testbench_hash"):
            with self.subTest(key=key):
                fx = self.fixture("G6")
                path, manifest = fx.manifest("G6", "metric_results")
                manifest["provenance"][key] = digest(f"changed-{key}")
                fx.save_manifest(path, manifest)
                gate = fx.report()["gates"]["G6"]
                self.assert_error_contains(gate, f"dependency_changed:{key}")
                self.assertEqual(gate["suggested_status"], "stale")

    def test_open_blocker_or_major_prevents_progression(self) -> None:
        for severity in ("BLOCKER", "MAJOR"):
            with self.subTest(severity=severity):
                fx = self.fixture("G6")
                review_path = resolve(fx.root, fx.state["gates"]["G6"]["review_record"])
                review = fx._read_json(review_path)
                review["findings"] = [
                    {
                        "finding_id": f"F-{severity}",
                        "severity": severity,
                        "status": "open",
                        "summary": "test finding",
                        "waiver_id": None,
                    }
                ]
                fx._write_json(review_path, review)
                fx.resign_review("G6")
                gate = fx.report()["gates"]["G6"]
                self.assert_error_contains(gate, f"open_{severity}")
                self.assertEqual(gate["suggested_status"], "blocked")

    def test_invalid_waiver_cannot_be_used(self) -> None:
        fx = self.fixture("G6")
        waiver = {
            "schema_version": "1.0.0",
            "waiver_id": "WVR-BAD",
            "project_id": "AFE-TEST",
            "gate_id": "G6",
            "severity": "MAJOR",
            "status": "active",
            "scope": {},
            "owner": None,
            "rationale": "",
            "compensating_controls": [],
            "expires_at": None,
            "revalidation_triggers": [],
            "approvals": [],
        }
        path = fx.root / "waivers" / "bad.json"
        fx._write_json(path, waiver)
        fx.state["gates"]["G6"]["waiver_records"] = [fx._rel(path)]
        gate = fx.report()["gates"]["G6"]
        for fragment in ("scope_missing", "human_owner_missing", "expiry_invalid", "insufficient_human_approvals"):
            self.assert_error_contains(gate, fragment)

    def test_valid_scoped_human_signed_waiver_is_accepted(self) -> None:
        fx = self.fixture("G6")
        waiver_id = fx.add_valid_waiver("G6", "F-MAJOR")
        review_path = resolve(fx.root, fx.state["gates"]["G6"]["review_record"])
        review = fx._read_json(review_path)
        review["findings"] = [
            {
                "finding_id": "F-MAJOR",
                "severity": "MAJOR",
                "status": "waived",
                "summary": "bounded exception",
                "waiver_id": waiver_id,
            }
        ]
        bundle = load_bundle(fx.state_path)
        records, load_errors = load_evidence_records(
            bundle, "G6", bundle.state["gates"]["G6"]
        )
        self.assertFalse(load_errors)
        review["scope_digest"] = compute_scope_digest(bundle, "G6", records)
        fx._write_json(review_path, review)
        fx.resign_review("G6")
        gate = fx.report()["gates"]["G6"]
        self.assertTrue(gate["eligible_for_human_close"], gate["errors"])
        self.assertEqual(gate["suggested_status"], "human_approval_required")

    def test_schematic_pvt_cannot_satisfy_pex_gate(self) -> None:
        fx = self.fixture("G8")
        source_path, source_manifest = fx.manifest("G6", "full_chain_pvt_evidence")
        replacement = copy.deepcopy(source_manifest)
        replacement.update(
            {
                "evidence_id": "EV-G8-SCHEMATIC-ONLY",
                "gate_id": "G8",
                "candidate_id": "AFE-TEST-G8-R1",
            }
        )
        replacement_path = fx.root / "evidence" / "G8-schematic-only.json"
        fx._write_json(replacement_path, replacement)
        fx.state["gates"]["G8"]["evidence_manifests"] = [fx._rel(replacement_path)]
        gate = fx.report()["gates"]["G8"]
        self.assert_error_contains(gate, "evidence_level_not_allowed")
        self.assert_error_contains(gate, "mandatory_artifact_missing:pex_candidate_manifest")

    def test_schematic_pvt_cannot_satisfy_tapeout_release_gate(self) -> None:
        fx = self.fixture("G10")
        _, source_manifest = fx.manifest("G6", "full_chain_pvt_evidence")
        replacement = copy.deepcopy(source_manifest)
        replacement.update(
            {
                "evidence_id": "EV-G10-SCHEMATIC-ONLY",
                "gate_id": "G10",
                "candidate_id": "AFE-TEST-G10-R1",
            }
        )
        replacement_path = fx.root / "evidence" / "G10-schematic-only.json"
        fx._write_json(replacement_path, replacement)
        fx.state["gates"]["G10"]["evidence_manifests"] = [fx._rel(replacement_path)]
        gate = fx.report()["gates"]["G10"]
        self.assert_error_contains(gate, "evidence_level_not_allowed")
        self.assert_error_contains(gate, "mandatory_artifact_missing:tapeout_release_manifest")

    def test_functional_ideal_proxy_cannot_satisfy_transistor_gate(self) -> None:
        fx = self.fixture("G5")
        path, manifest = fx.manifest("G5", "dc_pvt_evidence")
        manifest["contains_functional_proxy"] = True
        manifest["proxy_kinds"] = ["behavioral_cmfb"]
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G5"]
        self.assert_error_contains(gate, "functional_proxy_cannot_promote")

    def test_exploratory_next_phase_artifact_is_allowed_but_not_promotion(self) -> None:
        fx = self.fixture("G0")
        manifest_path = fx._create_manifest("G1", "specification_baseline")
        manifest = fx._read_json(manifest_path)
        manifest["exploratory_only"] = True
        manifest["promotion_eligible"] = False
        fx._write_json(manifest_path, manifest)
        fx.state["gates"]["G1"]["evidence_manifests"] = [fx._rel(manifest_path)]
        gate = fx.report()["gates"]["G1"]
        self.assertFalse(gate["errors"], gate["errors"])
        self.assertEqual(gate["suggested_status"], "not_started")

        manifest["promotion_eligible"] = True
        fx._write_json(manifest_path, manifest)
        gate = fx.report()["gates"]["G1"]
        self.assert_error_contains(gate, "future_artifact_marked_for_promotion")

    def test_old_project_data_cannot_be_current_validation(self) -> None:
        fx = self.fixture("G1")
        path, manifest = fx.manifest("G1", "adc_interface_contract")
        manifest["project_id"] = "OLD-AFE"
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G1"]
        self.assert_error_contains(gate, "evidence_project_id_mismatch")
        self.assert_error_contains(gate, "mandatory_artifact_missing:adc_interface_contract")

    def test_metric_extractor_change_requires_revalidation(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "metric_results")
        manifest["provenance"]["metric_extractor_hash"] = digest("extractor-v2")
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "dependency_changed:metric_extractor_hash")
        self.assertEqual(gate["suggested_status"], "stale")

    def test_pdk_change_requires_revalidation(self) -> None:
        fx = self.fixture("G3")
        path, manifest = fx.manifest("G3", "primitive_characterization")
        manifest["provenance"]["pdk"]["model_hash"] = digest("pdk-model-v2")
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G3"]
        self.assert_error_contains(gate, "dependency_changed:pdk.model_hash")
        self.assertEqual(gate["suggested_status"], "stale")

    def test_monte_carlo_provenance_requires_seed_and_sample_count(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "monte_carlo_evidence")
        del manifest["provenance"]["monte_carlo"]["seed"]
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "provenance_missing:monte_carlo.seed")

    def test_exploratory_artifact_cannot_fill_mandatory_slot(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "monte_carlo_evidence")
        manifest["exploratory_only"] = True
        manifest["promotion_eligible"] = False
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "mandatory_artifact_missing:monte_carlo_evidence")

    def test_only_valid_human_approval_allows_next_gate_to_start(self) -> None:
        fx = self.fixture("G1")
        fx.approve_gate("G1")
        fx.state["gates"]["G2"].update(
            {
                "status": "in_progress",
                "candidate_id": "AFE-TEST-G2-R1",
                "candidate_authors": ["designer-1"],
                "status_actor": {
                    "actor_type": "codex",
                    "actor_id": "codex-test",
                    "updated_at": "2030-01-01T00:00:00Z",
                },
            }
        )
        report = fx.report()
        self.assertTrue(report["gates"]["G1"]["effective_approved"])
        self.assertTrue(report["gates"]["G1"]["can_start_next_gate"])
        self.assertFalse(
            any("predecessor_not_human_approved" in e for e in report["gates"]["G2"]["errors"])
        )

    def test_tampered_human_signature_is_rejected(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        approval_path = resolve(fx.root, fx.state["gates"]["G0"]["approval_record"])
        approval = fx._read_json(approval_path)
        approval["scope_digest"] = digest("tampered-scope")
        fx._write_json(approval_path, approval)
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "approval_scope_digest_mismatch")
        self.assert_error_contains(gate, "signature_verification_failed")
        self.assertFalse(gate["effective_approved"])

    def test_policy_bundle_change_invalidates_old_evidence_and_approval(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        for key, source in (
            ("gate_policy", fx.gate_policy_path),
            ("evidence_policy", fx.evidence_policy_path),
            ("authorization_policy", fx.authorization_policy_path),
        ):
            copied = fx.root / "policies" / f"{key}.json"
            policy = load_data(source)
            if key == "evidence_policy":
                policy["description"] = f"{policy.get('description', '')} changed"
            fx._write_json(copied, policy)
            fx.state["policies"][key] = fx._rel(copied)
        report = fx.report()
        self.assertIn("current_baseline_policy_hash_mismatch", report["global_errors"])
        self.assertEqual(report["gates"]["G0"]["suggested_status"], "stale")
        self.assertFalse(report["gates"]["G0"]["effective_approved"])
        self.assertEqual(report["gates"]["G1"]["suggested_status"], "not_started")

    def test_review_change_after_approval_requires_new_approval_binding(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        review_path = resolve(fx.root, fx.state["gates"]["G0"]["review_record"])
        review = fx._read_json(review_path)
        review["findings"] = [
            {
                "finding_id": "F-LATE-MINOR",
                "severity": "MINOR",
                "status": "closed",
                "summary": "Review content changed after approval",
                "waiver_id": None,
            }
        ]
        fx._write_json(review_path, review)
        fx.resign_review("G0")
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "approval_review_digest_mismatch")
        self.assertFalse(gate["effective_approved"])

    def test_schema_violation_is_not_promotion_evidence(self) -> None:
        fx = self.fixture("G6")
        path, manifest = fx.manifest("G6", "metric_results")
        manifest["pretend_passed"] = True
        fx.save_manifest(path, manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "schema_violation")
        self.assert_error_contains(gate, "mandatory_artifact_missing:metric_results")

    def test_metric_in_wrong_artifact_type_cannot_satisfy_requirement(self) -> None:
        fx = self.fixture("G6")
        metric_path, metric_manifest = fx.manifest("G6", "metric_results")
        result = metric_manifest["metrics"].pop()
        fx.save_manifest(metric_path, metric_manifest)
        other_path, other_manifest = fx.manifest("G6", "full_chain_pvt_evidence")
        other_manifest["metrics"].append(result)
        fx.save_manifest(other_path, other_manifest)
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "controlling_metric_missing:REQ-GAIN")

    def test_open_change_control_blocks_affected_gate(self) -> None:
        fx = self.fixture("G6")
        change = {
            "schema_version": "1.0.0",
            "change_id": "ECO-17",
            "project_id": "AFE-TEST",
            "change_class": "netlist",
            "status": "revalidation_required",
            "owner": {"actor_type": "human", "actor_id": "eco-owner"},
            "affected_gates": ["G6"],
            "affected_candidates": ["AFE-TEST-G6-R1"],
            "reason": "Bias netlist changed",
            "before_fingerprints": {"netlist_hash": digest("netlist-v1")},
            "after_fingerprints": {"netlist_hash": digest("netlist-v2")},
            "invalidated_evidence_ids": ["EV-G6-metric_results"],
            "required_revalidation": ["rerun G6 metrics"],
            "verification_evidence_ids": [],
            "created_at": "2030-01-01T00:00:00Z",
            "closed_by": None,
        }
        path = fx.root / "changes" / "ECO-17.json"
        fx._write_json(path, change)
        fx.state["change_records"] = [fx._rel(path)]
        gate = fx.report()["gates"]["G6"]
        self.assert_error_contains(gate, "open_change_control:ECO-17")
        self.assertEqual(gate["suggested_status"], "blocked")

    def test_standalone_provenance_and_stale_checkers_match_gatekeeper(self) -> None:
        fx = self.fixture("G6")
        provenance = check_provenance(fx.state_path, "G6")
        staleness = check_staleness(fx.state_path, "G6")
        self.assertFalse(provenance["global_errors"])
        self.assertTrue(all(item["valid_provenance"] for item in provenance["evidence"]))
        self.assertFalse(any(item["stale"] for item in staleness["evidence"]))

        path, manifest = fx.manifest("G6", "metric_results")
        manifest["provenance"]["testbench_hash"] = digest("new-testbench")
        fx.save_manifest(path, manifest)
        staleness = check_staleness(fx.state_path, "G6")
        stale_ids = {item["evidence_id"] for item in staleness["evidence"] if item["stale"]}
        self.assertIn(manifest["evidence_id"], stale_ids)

    def test_verified_human_approval_is_observed_not_automatically_suggested(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        gate = fx.report()["gates"]["G0"]
        self.assertTrue(gate["effective_approved"])
        self.assertIsNone(gate["suggested_status"])

    def test_gate_approver_must_be_distinct_from_independent_reviewer(self) -> None:
        fx = self.fixture("G0")
        fx.approve_gate("G0")
        approval_path = resolve(fx.root, fx.state["gates"]["G0"]["approval_record"])
        approval = fx._read_json(approval_path)
        approval["approver"] = {
            "actor_type": "human",
            "actor_id": "reviewer-1",
            "role": "gate_approver",
            "signed_at": "2030-01-01T00:00:00Z",
        }
        fx._sign_actor(approval, approval["approver"], "gate_approval")
        fx._write_json(approval_path, approval)
        fx.state["gates"]["G0"]["status_actor"]["actor_id"] = "reviewer-1"
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "approver_is_independent_reviewer")
        self.assertFalse(gate["effective_approved"])

    def test_change_record_needs_verified_human_closure(self) -> None:
        fx = self.fixture("G0")
        change = {
            "schema_version": "1.0.0",
            "change_id": "ECO-CLOSED",
            "project_id": "AFE-TEST",
            "change_class": "policy",
            "status": "closed",
            "owner": {"actor_type": "human", "actor_id": "eco-owner"},
            "affected_gates": ["G0"],
            "affected_candidates": ["AFE-TEST-G0-R1"],
            "reason": "Governance policy clarification",
            "before_fingerprints": {"policy_hash": digest("policy-old")},
            "after_fingerprints": {"policy_hash": fx.baseline["policy_hash"]},
            "invalidated_evidence_ids": [],
            "required_revalidation": ["rerun governance checks"],
            "verification_evidence_ids": ["EV-G0-policy_snapshot"],
            "created_at": "2030-01-01T00:00:00Z",
            "closed_by": {
                "actor_type": "human",
                "actor_id": "approver-1",
                "role": "design_authority",
                "closed_at": "2030-01-01T00:00:00Z",
                "verification": {
                    "method": "ed25519",
                    "key_id": "approver-1",
                    "signature_base64": "AAAA",
                },
            },
        }
        path = fx.root / "changes" / "ECO-CLOSED.json"
        fx._write_json(path, change)
        fx.state["change_records"] = [fx._rel(path)]
        gate = fx.report()["gates"]["G0"]
        self.assert_error_contains(gate, "closure_signature_verification_failed")
        self.assertEqual(gate["suggested_status"], "blocked")

        fx._sign_actor(change, change["closed_by"], "change_record")
        fx._write_json(path, change)
        fx.save_state()
        bundle = load_bundle(fx.state_path)
        records, errors = load_evidence_records(bundle, "G0", bundle.state["gates"]["G0"])
        self.assertFalse(errors)
        review_path = resolve(fx.root, fx.state["gates"]["G0"]["review_record"])
        review = fx._read_json(review_path)
        review["scope_digest"] = compute_scope_digest(bundle, "G0", records)
        fx._write_json(review_path, review)
        fx.resign_review("G0")
        gate = fx.report()["gates"]["G0"]
        self.assertTrue(gate["eligible_for_human_close"], gate["errors"])

    def test_all_governance_clis_are_read_only_and_agree_on_valid_state(self) -> None:
        fx = self.fixture("G6")
        before = directory_digest(fx.root)
        commands = (
            ("gatekeeper.py", ["--gate", "G6", "--json"]),
            ("provenance_check.py", ["--gate", "G6", "--json"]),
            ("stale_evidence_check.py", ["--gate", "G6", "--json"]),
        )
        outputs = {}
        for script, extra in commands:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / script),
                    "--state",
                    str(fx.state_path),
                    *extra,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            outputs[script] = json.loads(completed.stdout)
        after = directory_digest(fx.root)
        self.assertEqual(before, after)
        self.assertTrue(outputs["gatekeeper.py"]["gate"]["eligible_for_human_close"])
        self.assertTrue(
            all(item["valid_provenance"] for item in outputs["provenance_check.py"]["evidence"])
        )
        self.assertFalse(
            any(item["stale"] for item in outputs["stale_evidence_check.py"]["evidence"])
        )

    def test_tapeout_release_requires_release_authority_role(self) -> None:
        fx = self.fixture("G10")
        fx.approve_gate("G10")
        approval_path = resolve(fx.root, fx.state["gates"]["G10"]["approval_record"])
        approval = fx._read_json(approval_path)
        approval["approver"]["role"] = "gate_approver"
        fx._sign_actor(approval, approval["approver"], "gate_approval")
        fx._write_json(approval_path, approval)
        gate = fx.report()["gates"]["G10"]
        self.assert_error_contains(gate, "approver_role_not_valid_for_gate")
        self.assertFalse(gate["effective_approved"])

    def test_repeated_evaluation_does_not_mutate_loaded_policy(self) -> None:
        fx = self.fixture("G6")
        bundle = load_bundle(fx.state_path)
        before = copy.deepcopy(bundle.evidence_policy)
        first = evaluate_project(bundle)
        middle = copy.deepcopy(bundle.evidence_policy)
        second = evaluate_project(bundle)
        self.assertEqual(before, middle)
        self.assertEqual(before, bundle.evidence_policy)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
