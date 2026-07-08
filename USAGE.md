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
Use $afe-analog-design-flow to continue this neural recording AFE design from
the current handoff.
```

## Typical Workflows

### Continue From A Handoff

Provide the current handoff and ask Codex to identify:

- Current phase.
- Accepted evidence.
- Rejected branches.
- Open risks.
- Smallest next experiment.

### Audit A Passing Candidate

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

### Check Candidate Report Completeness

Use:

```bash
python skills/afe-analog-design-flow/scripts/candidate_report_check.py <candidate-run-dir>
```

Use `--strict` in automation if missing required evidence should return a
non-zero exit code.

## Module Reporting Rule

Each completed small module should produce a short report and result images
before it is used as full-chain evidence. A module report should include:

- Scope and topology.
- Source netlist and testbench.
- PVT/corners.
- Passed and failed gates.
- Key metrics and worst corner.
- Result image paths.
- Open risks and next step.

## Forward Testing

Before publishing a modified version of the skill, use:

```text
skills/afe-analog-design-flow/references/forward-test-prompts.md
```

Run the prompts in fresh threads or subagents, passing raw artifacts rather
than expected answers.

## Contact

Maintainer: HC Wang  
Email: [hcwang@hdu.edu.cn](mailto:hcwang@hdu.edu.cn)

