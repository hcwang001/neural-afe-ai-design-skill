# Governed AFE Development Workflow

## Purpose And Authority

This reference explains the lifecycle implemented by
`governance/policies/default-gates.yaml`. The machine-readable policy is
controlling when prose and policy differ.

Simulation completion is not gate closure. A gate closes only for the exact
candidate revision and scope digest covered by a valid independent review and a
verified human approval record. Codex and automation may report readiness but
must not create that approval.

## Common Entry And Exit Rules

Every gate entry requires:

1. An instantiated, non-template project state.
2. The predecessor gate in effective `approved` state, backed by a human
   approval record whose scope digest still matches current evidence.
3. Current policy, source, specification, requirements, PDK/model, and toolchain
   baselines.
4. No attempt to use other-project, other-candidate, stale, functional-proxy,
   or `exploratory_only` material as promotion evidence.

Every gate presented for human closure requires:

1. All policy-mandated artifacts represented by valid evidence manifests.
2. Semantic evaluation of every controlling requirement applicable to the
   gate, using values and units parsed from current evidence.
3. No open BLOCKER or MAJOR finding/risk.
4. Valid provenance and no stale promotion evidence.
5. Valid, non-expired waivers for every waived criterion; BLOCKER is not
   waivable under the default policy.
6. A completed independent human review bound to the current scope digest.
7. `gatekeeper.py` reporting `eligible_for_human_close: true`.

The gatekeeper may recommend `human_approval_required`. Only a separately
verified human approval may make `approved` effective.

## State And Parallel Work

Automation-controlled states are `in_progress`, `review_ready`,
`human_approval_required`, `changes_required`, `blocked`, and `stale`.
`not_started` is a system/initial state; `approved` is human-only.

If G(n) is not effectively human approved:

- G(n+1) remains `not_started`;
- parallel G(n+1) analysis is allowed only with `exploratory_only: true` and
  `promotion_eligible: false` in every evidence manifest;
- exploratory work cannot satisfy a mandatory artifact or controlling metric;
- later approval of G(n) does not automatically promote earlier exploratory
  artifacts. They must be rebased, revalidated, and issued as new evidence.

## G0: Governance Baseline

Entry: a project has been created but has no authoritative lifecycle state.

Mandatory outputs:

- instantiated project state and policy snapshot;
- human role assignments for design owner, independent reviewer, gate approver,
  waiver authority, interface owners, and release authority;
- approved internal/public data boundary and PDK confidentiality plan.

Exit intent: establish who may perform each human action and which machine
contracts control the project. G0 contains no circuit approval.

## G1: Requirements And Interface Baseline

Entry: G0 is effectively human approved.

Mandatory outputs:

- controlling versus preference requirements with owner, comparator, value,
  unit, applicable gates, and required evidence type;
- evidence/verification plan;
- electrode, ADC, PMU, and top-level interface contracts;
- signal range, gain, bandwidth, noise, power, area, input impedance,
  common-mode, rejection, startup/recovery, yield, test, and layout targets as
  applicable to the project.

Provisional or inferred values may be recorded as proposals, but cannot become
the controlling baseline without human specification ownership.

## G2: Architecture Selection

Entry: G1 is effectively human approved.

Mandatory outputs:

- architecture matrix covering noise, power, area, gain allocation, bandwidth,
  input/backend loading, offset, loops, pseudoR/well-bias, testability, and
  manufacturability;
- retained rejected alternatives and reasons;
- architecture decision record, block allocation, and risk register.

Behavioral or literature results support the decision but do not prove a
transistor implementation.

## G3: Primitive And Model Qualification

Entry: G2 is effectively human approved.

Mandatory outputs:

- PDK/model manifest and applicable sections;
- MOS gm/Id, gm/gds, operating region, capacitance, noise, leakage, matching,
  reliability, and area data over the project-approved conditions;
- passive value/spread/noise/parasitic/voltage/area data;
- pseudoR and well-bias terminal, leakage, startup, noise, and PEX applicability;
- documented model validity limits.

Project-specific corners and device rules belong in the approved project
overlay, not in the generic lifecycle.

## G4: Behavioral Model And Verification Baseline

Entry: G3 is effectively human approved.

Mandatory outputs:

- full-chain gain/noise/loading/power/area budget;
- loop/plant models for CMFB, servo, well-bias, compensation, high-pass, and
  backend interactions;
- assumption register and correlation plan;
- verification-plan mapping from controlling requirement to testbench and
  evidence level.

Models must include the suspected failure mechanism. Measured-port updates are
preferred once transistor data exists.

## G5: Block Schematic Candidate

Entry: G4 is effectively human approved.

Technical sequence:

1. Implement the smallest block that tests the hypothesis.
2. Run DC and operating-region checks first across approved conditions.
3. Run AC/noise/rejection/stability only for DC-clean cases.
4. Run startup/reset/recovery for loops, high-Z, leakage, storage, and bias
   blocks.
5. Replace functional ideal compensation/filter/passive elements with intended
   PDK devices, including distributed parasitics where material.
6. Compare with the behavioral model and record correlation.

Mandatory evidence includes module reports, source/testbench provenance,
DC/PVT, operating region, relevant noise/stability/recovery/interface results,
and a functional-ideal audit. A block report or plot alone is not authorization.

## G6: Integrated Schematic Candidate

Entry: all required G5 block candidates are effectively human approved.

Mandatory evidence includes:

- exact integrated schematic candidate manifest;
- deterministic full-chain PVT;
- parsed controlling metrics;
- deterministic mismatch and mismatch-aware CMRR/PSRR;
- foundry Monte-Carlo with recorded model section, seed, sample count, parsing
  count, failures, and distribution statistics;
- correct differential/common-mode stability, startup/recovery, high-Z, device
  reliability, and functional-ideal audits.

Closing G6 creates an approved schematic candidate only. It does not establish
layout readiness, PEX validity, post-layout signoff, or tapeout release.

## G7: Layout-Ready Candidate

Entry: G6 is effectively human approved.

Mandatory outputs include:

- schematic freeze/candidate linkage;
- layout constraints, floorplan, matching/symmetry/shielding strategy, area
  basis, and pre-layout parasitic stress;
- high-Z and reliability closure for layout implementation;
- test/trim/calibration architecture and observability;
- ESD/pad plan and closed electrode/ADC/PMU/top-level implementation contracts;
- PEX and DFM plans.

The floorplan must show physical intent and exclude simulation-only proxies.
G7 closure authorizes layout work for the exact candidate; it is not PEX or
post-layout evidence.

## G8: PEX Candidate

Entry: G7 is effectively human approved.

Mandatory outputs include DRC/LVS results, layout digest, extraction-deck
identity, PEX netlist digest, extraction manifest, and initial extracted sanity
checks. Schematic PVT cannot substitute for any G8 artifact.

Closing G8 identifies the extracted candidate to be verified. It does not
authorize a post-layout signoff claim.

## G9: Post-Layout Signoff Candidate

Entry: G8 is effectively human approved.

Mandatory evidence includes post-layout DC/PVT, gain/bandwidth, noise, correct
loop stability, startup/recovery, mismatch-aware rejection, post-layout MC,
post-fill extraction where applicable, device reliability, DFM, and extracted
test/ESD/interface verification.

All controlling metrics are re-evaluated from extracted evidence. Pre-layout or
schematic evidence may be retained for comparison but cannot satisfy G9
mandatory artifacts. The default policy requires a `signoff_reviewer` for G9.

## G10: Tapeout Release

Entry: G9 is effectively human approved.

Mandatory outputs include the immutable release manifest/BOM, layout and
netlist digests, foundry-deck manifest, signoff summary, waiver summary,
interface release, and data-integrity report. No open BLOCKER or MAJOR may be
present. Under the default machine policy, the approving role for G10 is specifically
`release_authority`; a general gate approver cannot release it. Organizations
may impose an additional protected-branch or release-system quorum outside this
single-record gate model.

The skill and gatekeeper can assemble or validate a draft package. They cannot
authorize tapeout release.

## Evidence Freshness And Change Control

Evidence is valid only for the baseline recorded in its manifest. Changes to
source, specification, netlist/includes, testbench/stimulus, metric extractor,
PDK/model/section, simulator/command profile, layout, extraction deck, PEX, or
policy invalidate dependent evidence. Old approvals remain historical records
but cease to be effective for the changed scope.

A frozen baseline change requires an ECO/change record with before/after
digests, impact analysis, stale-evidence set, regression plan, and human owner.
An applicable record remains gate-blocking until revalidation is present and a
verified human change authority closes or cancels it. Editing a handoff cannot
substitute for change control.

## Preserved Technical Lessons

- Stop repeated sizing sweeps when the failure is structural.
- Standalone CMFB screens do not replace integrated plant validation.
- Map compensation by mechanism, not nominal `R*C` alone.
- Include local pseudoR/well-bias and auxiliary circuits in noise, area, startup,
  reliability, and matching decisions.
- Separate signal bandwidth, stage bandwidth, CMFB crossover, pseudoR/high-pass,
  and backend settling.
- Use mismatch-aware rejection and consistent area basis.
- Treat handoffs as derived navigation aids, not authoritative state.
