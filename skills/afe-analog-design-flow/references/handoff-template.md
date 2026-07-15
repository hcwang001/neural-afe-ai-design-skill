# Derived Handoff Template

## Status And Authority

This handoff is a read-only view generated from project state and gatekeeper
output. It must not be edited to change lifecycle state. Statements such as
"passed", "approved", or "final" have no authority unless the referenced gate
has an effective human approval record for the displayed scope digest.

```markdown
# AFE Project Handoff - <generated UTC timestamp>

## Governance Snapshot

- Project ID: <from project state>
- State revision: <from project state>
- Source state file: <path>
- Gate policy ID/version: <from policy>
- Evidence policy ID/version: <from policy>
- Authorization policy ID/version: <from policy>
- Policy/schema contract hash: <current baseline policy_hash>
- Generator version/hash: <tool identity>
- This report is authoritative: no

## Current Gate Evaluation

- Gate ID/name: <from gatekeeper>
- Candidate ID: <from project state>
- Candidate stage: governance baseline / requirements baseline / architecture
  candidate / primitive baseline / behavioral baseline / block schematic
  candidate / integrated schematic candidate / layout-ready candidate / PEX
  candidate / post-layout signoff candidate / tapeout release package
- Recorded status: <from project state>
- Gatekeeper enforcement/recommendation: <`not_started` enforcement, an allowed
  automation state, or none when a human approval is merely observed>
- Scope digest: <gatekeeper-computed digest>
- Eligible for human close: <true/false from gatekeeper>
- Effective human approval observed: <true/false from gatekeeper>
- Can next gate start: <true/false from gatekeeper>

Do not manually alter the preceding values.

## Predecessor Authorization

| predecessor | effective approval | approval record | scope current |
|---|---|---|---|
| <derived> | <derived> | <reference or none> | <derived> |

## Baseline Fingerprints

- Source commit:
- Spec hash:
- Netlist/include hash:
- Testbench/stimulus hash:
- PDK ID/release/model hash/sections:
- Simulator/version/executable hash:
- Command profile hash:
- Metric extractor hash:
- Layout hash, when applicable:
- PEX/extraction-deck hash, when applicable:

## Requirements Traceability

| requirement ID | controlling/preference | comparator | current parsed value | unit | evidence ID | evaluation |
|---|---|---|---:|---|---|---|
| <derived> | | | | | | |

## Mandatory Artifact Evaluation

| artifact type | evidence ID | evidence level | promotion eligible | provenance valid | current/stale |
|---|---|---|---|---|---|
| <derived> | | | | | |

- Missing mandatory artifact types: <derived list>
- Exploratory-only artifacts: <derived list; explicitly excluded from promotion>
- Functional ideal/proxy findings: <derived list>

## Independent Review And Findings

- Review record: <reference or none>
- Review status: <derived>
- Reviewer identity/signature verification: <derived; never invented>

| finding ID | severity | status | waiver ID | owner/next action |
|---|---|---|---|---|
| <derived> | | | | |

## Waivers And Risks

- Valid active waivers: <derived>
- Invalid/expired waivers: <derived>
- Open BLOCKER risks: <derived>
- Open MAJOR risks: <derived>
- Open MINOR risks: <derived>

## Technical Snapshot

- Architecture and active topology:
- DC/PVT and operating-region summary:
- Gain/bandwidth/noise summary:
- Mismatch-aware CMRR/PSRR summary:
- Stability and startup/recovery summary:
- High-Z and pseudoR/well-bias summary:
- Reliability/voltage-domain summary:
- Area/floorplan/layout-readiness summary:
- MC status, when mandatory:
- PEX/post-layout status, when mandatory:
- Test/trim/calibration and ESD/interface status, when mandatory:

Every value above must cite an evidence ID; a path or plot alone is insufficient.

## Decisions And Changes

- Decision record IDs:
- ECO/change-control IDs:
- Rejected alternatives retained:
- Current limiting mechanism:
- Proposed next action:

The proposed action is not authorization to start a gate whose predecessor is
not effectively human approved. Such work must remain exploratory-only.
```
