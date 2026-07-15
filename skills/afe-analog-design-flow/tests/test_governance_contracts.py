from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


SKILL_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = SKILL_ROOT / "governance"
POLICIES = GOVERNANCE / "policies"
SCHEMAS = GOVERNANCE / "schemas"
TEMPLATES = GOVERNANCE / "templates"
REFERENCES = SKILL_ROOT / "references"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} does not contain a mapping")
    return value


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class GovernanceContractTests(unittest.TestCase):
    def test_every_json_schema_is_valid_draft_2020_12(self) -> None:
        schemas = sorted(SCHEMAS.glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 10)
        for path in schemas:
            with self.subTest(schema=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                Draft202012Validator.check_schema(schema)

    def test_all_policies_and_templates_are_parseable_mappings(self) -> None:
        paths = sorted(POLICIES.glob("*.yaml")) + sorted(TEMPLATES.glob("*.yaml"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsInstance(load_yaml(path), dict)

    def test_gate_policy_has_explicit_non_bypassable_entry_exit_contract(self) -> None:
        policy = load_yaml(POLICIES / "default-gates.yaml")
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
        self.assertEqual(
            set(policy["criteria_contract"]["human_close_eligible_requires"]),
            required_readiness,
        )
        order = policy["gate_order"]
        self.assertEqual(order, [f"G{number}" for number in range(11)])
        previous = None
        for gate_id in order:
            definition = policy["gates"][gate_id]
            with self.subTest(gate=gate_id):
                self.assertEqual(definition["predecessor"], previous)
                self.assertTrue(definition["entry_criteria"])
                self.assertEqual(
                    set(definition["exit_criteria"]),
                    {"human_close_eligible", "verified_human_approval"},
                )
                self.assertTrue(definition["mandatory_artifacts"])
                self.assertTrue(definition["required_review_roles"])
                self.assertTrue(definition["required_approval_roles"])
            previous = gate_id
        self.assertEqual(policy["gates"]["G9"]["required_review_roles"], ["signoff_reviewer"])
        self.assertEqual(policy["gates"]["G10"]["required_review_roles"], ["signoff_reviewer"])
        self.assertEqual(policy["gates"]["G10"]["required_approval_roles"], ["release_authority"])

    def test_candidate_stages_are_distinct(self) -> None:
        gates = load_yaml(POLICIES / "default-gates.yaml")["gates"]
        self.assertEqual(gates["G6"]["candidate_stage"], "schematic_candidate")
        self.assertEqual(gates["G7"]["candidate_stage"], "layout_ready_candidate")
        self.assertEqual(gates["G8"]["candidate_stage"], "pex_candidate")
        self.assertEqual(
            gates["G9"]["candidate_stage"], "post_layout_signoff_candidate"
        )
        self.assertEqual(gates["G10"]["candidate_stage"], "tapeout_release_package")
        self.assertEqual(len({gates[key]["candidate_stage"] for key in gates}), len(gates))

    def test_mc_pex_test_and_esd_become_mandatory_at_defined_gates(self) -> None:
        gates = load_yaml(POLICIES / "default-gates.yaml")["gates"]
        self.assertNotIn("monte_carlo_evidence", gates["G5"]["mandatory_artifacts"])
        self.assertIn("monte_carlo_evidence", gates["G6"]["mandatory_artifacts"])
        self.assertIn("pex_plan", gates["G7"]["mandatory_artifacts"])
        self.assertIn("pex_netlist", gates["G8"]["mandatory_artifacts"])
        self.assertIn(
            "post_layout_monte_carlo_evidence", gates["G9"]["mandatory_artifacts"]
        )
        self.assertIn("test_trim_calibration_plan", gates["G7"]["mandatory_artifacts"])
        self.assertIn("esd_pad_plan", gates["G7"]["mandatory_artifacts"])
        self.assertIn("test_interface_verification", gates["G9"]["mandatory_artifacts"])
        self.assertIn("esd_interface_verification", gates["G9"]["mandatory_artifacts"])

    def test_external_interfaces_are_mandatory_and_later_closed(self) -> None:
        gates = load_yaml(POLICIES / "default-gates.yaml")["gates"]
        for interface in ("electrode", "adc", "pmu", "top_level"):
            self.assertIn(
                f"{interface}_interface_contract", gates["G1"]["mandatory_artifacts"]
            )
        self.assertIn("interface_closure", gates["G7"]["mandatory_artifacts"])
        self.assertIn("interface_release", gates["G10"]["mandatory_artifacts"])

    def test_automation_authorization_is_closed_set(self) -> None:
        policy = load_yaml(POLICIES / "default-authorization.yaml")
        allowed = {
            "in_progress",
            "review_ready",
            "human_approval_required",
            "changes_required",
            "blocked",
            "stale",
        }
        self.assertEqual(set(policy["automation_allowed_gate_states"]), allowed)
        self.assertNotIn("approved", policy["automation_allowed_gate_states"])
        self.assertEqual(policy["human_only_gate_states"], ["approved"])
        self.assertTrue(policy["review"]["require_independence"])
        self.assertTrue(policy["approval"]["require_distinct_from_reviewer"])
        self.assertEqual(policy["signature"]["supported_methods"], ["ed25519"])

    def test_evidence_policy_covers_identity_freshness_and_mc_seed(self) -> None:
        policy = load_yaml(POLICIES / "default-evidence.yaml")
        common = set(policy["required_provenance"]["all"])
        self.assertTrue(
            {"source_commit", "evidence_commit", "spec_hash", "timestamp_utc", "policy_hash"}.issubset(common)
        )
        transistor = set(policy["required_provenance"]["transistor_schematic"])
        self.assertTrue(
            {
                "netlist_hash",
                "testbench_hash",
                "pdk.model_hash",
                "simulator.executable_hash",
                "command",
                "metric_extractor_hash",
            }.issubset(transistor)
        )
        monte_carlo = set(policy["required_provenance"]["monte_carlo"])
        self.assertTrue(
            {"monte_carlo.seed", "monte_carlo.sample_count", "monte_carlo.statistical_section"}.issubset(monte_carlo)
        )
        freshness = set(policy["freshness_dependencies"])
        self.assertTrue(
            {"source_commit", "spec_hash", "netlist_hash", "testbench_hash", "metric_extractor_hash", "policy_hash"}.issubset(freshness)
        )

    def test_templates_cannot_pretend_to_be_human_authorization(self) -> None:
        state = load_yaml(TEMPLATES / "project-state.yaml")
        self.assertTrue(state["template_only"])
        self.assertTrue(all(gate["status"] == "not_started" for gate in state["gates"].values()))
        self.assertEqual(load_yaml(TEMPLATES / "gate-review.yaml")["reviewer"], None)
        self.assertEqual(load_yaml(TEMPLATES / "waiver.yaml")["approvals"], [])
        evidence = load_yaml(TEMPLATES / "evidence-manifest.yaml")
        self.assertEqual(evidence["object_kind"], "analysis_result")
        self.assertFalse(evidence["promotion_eligible"])
        self.assertTrue(evidence["exploratory_only"])
        combined = "\n".join(path.read_text(encoding="utf-8") for path in TEMPLATES.glob("*.yaml"))
        self.assertNotIn("status: approved", combined)
        self.assertNotIn("signature_base64:", combined)
        self.assertNotIn("[x]", combined.lower())

    def test_uninstantiated_project_template_fails_closed(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "gatekeeper.py"),
                "--state",
                str(TEMPLATES / "project-state.yaml"),
                "--gate",
                "G0",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn("project_state_is_template_only", report["global_errors"])
        self.assertFalse(report["gate"]["eligible_for_human_close"])

    def test_publication_and_project_reviews_are_separate_authority_domains(self) -> None:
        publication = (REFERENCES / "publication-review.md").read_text(encoding="utf-8")
        project = (REFERENCES / "project-gate-review.md").read_text(encoding="utf-8")
        routing = (REFERENCES / "review-checklist.md").read_text(encoding="utf-8")
        self.assertIn("must not be cited as project design evidence", publication)
        self.assertIn("does not itself approve a gate", project)
        self.assertIn("Deprecated Combined Checklist", routing)

    def test_default_governance_does_not_embed_project_numeric_heuristics(self) -> None:
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in POLICIES.glob("*.yaml"))
        for project_specific_token in ("tt27", "ss85", "ff85", "300 hz", "10 khz", "phase margin 60"):
            self.assertNotIn(project_specific_token, combined)

    def test_candidate_report_checker_is_read_only_non_authoritative_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate_report.md").write_text(
                "# Report\nkey metrics: gain failed requirement\n", encoding="utf-8"
            )
            before = tree_digest(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "candidate_report_check.py"),
                    str(root),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after = tree_digest(root)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(before, after)
        self.assertIn("authoritative: false", completed.stdout)
        self.assertIn("readiness conclusion: none", completed.stdout)
        self.assertIn("--strict has no gate meaning", completed.stdout)
        self.assertNotIn("[x]", completed.stdout.lower())

    def test_skill_entrypoint_preserves_engineering_and_authority_rules(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        for token in (
            "dc first",
            "architecture",
            "primitive",
            "behavioral",
            "mismatch-aware cmrr/psrr",
            "high-z",
            "pseudor",
            "reliability",
            "pex",
            "test/trim/calibration",
            "floorplan",
        ):
            self.assertIn(token, skill)
        self.assertIn("must never", skill)
        self.assertIn("write `approved`", skill)


if __name__ == "__main__":
    unittest.main()
