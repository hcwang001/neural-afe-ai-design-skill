# Usage

This repository contains a Codex skill at:

```text
skills/afe-analog-design-flow
```

## Install Locally

Copy the skill folder into your Codex skills directory:

```powershell
Copy-Item -Recurse .\skills\afe-analog-design-flow "$env:USERPROFILE\.codex\skills\afe-analog-design-flow"
```

On macOS/Linux, the equivalent path is usually:

```bash
cp -R skills/afe-analog-design-flow ~/.codex/skills/afe-analog-design-flow
```

Then start a new Codex thread and ask:

```text
Use $afe-analog-design-flow in governed mode. Load the instantiated project
state and run the gatekeeper before proposing work. Do not infer approval from
the handoff.
```

Install the governance runtime dependencies before using the validators:

```bash
python -m pip install -r skills/afe-analog-design-flow/requirements.txt
```

The gatekeeper fails closed if JSON Schema or signature-verification support is
unavailable.

## Typical Workflows

### Continue From Project State

Provide the current project state plus its referenced policies/manifests. A
handoff may be provided as a derived navigation aid. Ask Codex to identify:

- Current phase.
- Current promotion evidence as classified by manifests and gatekeeper.
- Rejected branches.
- Open risks.
- Smallest next experiment.

If the predecessor gate is not effectively human approved, the next gate must
remain `not_started`; parallel work must be exploratory-only.

### Audit A Candidate With Apparently Passing Metrics

Ask Codex to check whether a schematic-passing candidate is really ready to be
called tapeout-oriented. It should distinguish:

- Schematic PVT evidence.
- Deterministic mismatch evidence.
- MC evidence.
- PEX/post-layout evidence.
- Test, trim, calibration, ESD, and DFM readiness.

### Review pseudoR / Well-Bias Connectivity

Use:

```bash
python skills/afe-analog-design-flow/scripts/pseudor_connectivity_audit.py <netlist.scs>
```

This creates a first-pass table for pseudoR-like instances and assumed
`PSUB/DNW/PWELL/A/B` node mapping. The table is not signoff by itself; it is a
way to make manual connectivity review harder to skip.

### Inventory Candidate-Like Files

Use:

```bash
python skills/afe-analog-design-flow/scripts/candidate_report_check.py <candidate-run-dir>
```

This command performs discovery only. Filename/content hits do not validate
metrics, provenance, freshness, review, or gate state. `--strict` is deprecated.

### Evaluate A Gate

```bash
python skills/afe-analog-design-flow/scripts/provenance_check.py --state <project-state.yaml>
python skills/afe-analog-design-flow/scripts/stale_evidence_check.py --state <project-state.yaml>
python skills/afe-analog-design-flow/scripts/gatekeeper.py --state <project-state.yaml> --gate G6
```

The gatekeeper may report `human_approval_required`. It never writes
`approved`, completes independent review, or creates a signature.

## Module Reporting Rule

Each completed small module should produce a short report and result images
before it is used as full-chain evidence. A module report should include:

- Scope and topology.
- Source netlist and testbench.
- PVT/corners.
- Passed and failed simulation/metric checks, explicitly distinguished from
  lifecycle gate authorization.
- Key metrics and worst corner.
- Result image paths.
- Open risks and next step.

## Forward Testing

Before publishing a modified version of the skill, use:

```text
skills/afe-analog-design-flow/references/forward-test-prompts.md
```

Run the automated governance tests first. Prompt tests are qualitative checks
only and do not establish lifecycle correctness.

## Contact

Maintainer: HC Wang  
Email: [hcwang@hdu.edu.cn](mailto:hcwang@hdu.edu.cn)
