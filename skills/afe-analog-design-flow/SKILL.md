---
name: afe-analog-design-flow
description: Phase-gated analog front-end AFE design workflow for Codex. Use when planning, continuing, auditing, or packaging a neural-recording/biopotential AFE project from specifications through literature review, architecture selection, device/PDK characterization, behavioral modeling, decision rules for when to continue/stop/switch topology, transistor implementation, Spectre verification, tapeout-readiness constraints, device reliability, PEX/post-layout planning, test/trim/calibration planning, area/power/noise comparison, plots, layout/floorplan suggestion images, Monte-Carlo, or handoff generation.
---

# Neural Recording AFE Design Flow

Use this skill to run an AFE design as a disciplined engineering program, not
as a transcript replay. The intended flow is: define metrics, learn the
literature, compare multiple feasible architectures, characterize devices and
passives, build system and circuit-level behavioral models, then implement and
verify transistor blocks with DC-first Spectre gates.

## Quick Start

1. Locate context, but do not blindly continue it.
   - Find the newest handoff and the relevant older handoffs.
   - Extract constraints, accepted measurements, failed branches, and lessons.
   - Reframe the next step inside the phase-gated flow below.
2. Define the comparison target before changing circuits.
   - Record gain, bandwidth, input-referred noise, power, area, input impedance,
     common-mode range, CMRR, PSRR, offset/startup, MC yield, and layout risk.
   - Separate hard must-pass metrics from preference metrics.
3. Build an architecture shortlist.
   - Find literature and local prior art.
   - Compare at least two plausible system/circuit architectures when the
     architecture is not already frozen.
4. Characterize primitives before sweeping full circuits.
   - Create gm/Id, capacitance, noise, leakage, pseudoR, resistor, and area
     tables that bound what the PDK can realistically deliver.
5. Model the system before transistor trial-and-error.
   - Build behavior models for each candidate architecture.
   - Use models to allocate block specs and identify sensitive poles/loops.
6. Implement transistor blocks only after the target is clear.
   - Run module DC first.
   - Run AC/noise/rejection only for DC-passing cases.
   - Promote to full-chain only after module behavior matches the model.
   - After each small module is completed, generate module-level simulation
     result images and a short report before moving on.
   - Audit functional ideal elements before making any performance claim.
7. Report with evidence.
   - Use mismatch-aware CMRR/PSRR for claims.
   - Keep area basis consistent.
   - Apply tapeout-ready constraints before calling any circuit final.
   - Close each branch with a decision-rules review.
   - Generate a symmetry-aware overall layout/floorplan suggestion image before
     the final handoff.
   - Leave a handoff with exact files, metrics, risks, and next step.

## Reference Routing

Read only the references needed for the current task:

- `references/workflow.md`: phase-gated end-to-end design flow.
- `references/decision-rules.md`: decision rules for when to continue,
  stop sweeping, switch topology, or promote a candidate.
- `references/specs-and-architecture.md`: metrics, literature review, and
  architecture comparison.
- `references/device-sweeps-and-tables.md`: PDK primitive characterization and
  parameter tables.
- `references/behavioral-modeling.md`: system, loop, and measured-port models.
- `references/design-casebook.md`: curated project decisions, failure modes,
  and reusable AFE design lessons.
- `references/block-playbook.md`: block-level guidance for stage-1, stage-2,
  CMFB, pseudoR, well-bias, and backend interface work.
- `references/simulation-gates.md`: DC/PVT/noise/rejection/STB/startup/MC order
  and pass/fail conventions.
- `references/netlist-patterns.md`: netlist cleanup, dependency control, naming,
  and public artifact rules.
- `references/pseudo-resistor-well-bias.md`: pseudoR1/pseudoR2, PSUB/DNW/PWELL
  connectivity, and well-bias driver strategy.
- `references/area-and-comparison.md`: area accounting and literature table
  update rules.
- `references/layout-floorplan.md`: final physical-block layout suggestion
  image rules.
- `references/tapeout-ready-constraints.md`: device sizing, reliability,
  layout feasibility, PEX, startup/recovery, test, trim, calibration, ESD, and
  DFM rules for promoting a circuit toward tapeout.
- `references/plots-and-reporting.md`: gain/noise/CMRR/PSRR plots and final
  report formatting.
- `references/handoff-template.md`: compact template for final handoffs.
- `references/review-checklist.md`: pre-publication and human-review checklist.
- `references/forward-test-prompts.md`: fresh-thread prompts for validating
  whether the skill generalizes before GitHub publication.

## Phase Gates

1. **Spec and evidence gate**
   - Define must-pass and stretch metrics before architecture or sizing work.
   - Specify what evidence is acceptable for each metric: literature, behavior
     model, standalone transistor simulation, full-chain PVT, MC, or layout.
2. **Literature and architecture gate**
   - Produce an architecture matrix with at least noise, power, area, gain,
     bandwidth, input impedance, CMRR/PSRR, offset handling, complexity, and
     manufacturability.
   - Keep rejected architectures with explicit reasons.
3. **Primitive characterization gate**
   - Build or update device/passive lookup tables before broad circuit sweeps.
   - Use these tables to choose realistic gm/Id, W/L, current density, resistor,
     capacitor, pseudoR, and well-bias ranges.
4. **Behavioral model gate**
   - Build a chain budget for each viable architecture.
   - Build focused loop/plant models for sensitive blocks such as CMFB,
     pseudoR/well-bias, high-pass corners, and backend loading.
   - Prefer measured-port models after transistor-level data exists.
5. **Block implementation gate**
   - Implement one block at a time.
   - Verify DC, operating region, power, noise, loop stability, and interfaces.
   - Save module-level simulation plots/images and a short module report for
     every completed block.
   - Do not run full-chain sweeps to debug a block-level unknown.
6. **Full-chain integration gate**
   - Run deterministic PVT full-chain checks.
   - Verify input/output common-mode, gain, fHP/fLP, noise, CMRR, PSRR, and
     startup.
7. **Variation and layout gate**
   - Run deterministic mismatch, then foundry MC.
   - Update area using the same topology as the electrical run.
   - Generate an overall physical-block floorplan suggestion image.
   - Mark final numbers as pre-layout or layout-aware.
8. **Tapeout-candidate gate**
   - Read `references/tapeout-ready-constraints.md`.
   - Audit MOS sizing, reliability, voltage domains, high-Z nodes, bias plans,
     capacitor/resistor layout feasibility, startup/recovery, PEX path, test
     hooks, trim/calibration, ESD/top-level interfaces, and DFM risks.
   - Do not call a candidate tapeout-ready from schematic PVT alone.

## Core Invariants

- Do not continue a branch just because it is the latest transcript state.
- Do not optimize a metric until the dominant mechanism is identified.
- Do not promote a candidate unless it passes the appropriate gate without
  functional ideal aids.
- Do not keep sweeping device sizes when the failure pattern indicates a
  topology, leakage, matching, or reference-path limitation.
- Do not run blind sweeps when the limiting mechanism is unknown.
- Do not trust a behavioral model that omits the suspected failure mechanism.
- Read `references/design-casebook.md` before re-opening a topology that was
  previously paused, rejected, or demoted.
- Do not claim nominal/symmetric CMRR or PSRR externally. Use deterministic
  mismatch curves or MC distributions.
- For pseudoR devices, explicitly audit terminal order and node intent:
  `PSUB`, `DNW`, `PWELL`, `A`, `B`.
- For well-bias, distinguish slow leakage compensation from wideband buffering.
- Do not present an area treemap as a layout suggestion. A floorplan must show
  signal flow, differential symmetry, common-mode islands, local feedback loops,
  and proxy exclusions.
- Do not promote a candidate solely because schematic PVT passes. It must be
  physically realizable, reliability-clean, mismatch-aware, startup-safe, and
  backed by a PEX and test/trim plan when moving toward tapeout.
- Keep scripts and netlists reproducible; avoid hard-coded local-only paths in
  GitHub-ready artifacts.
- Do not publish PDK files, foundry model files, raw PEX netlists, PSF data,
  Spectre raw databases, or private paper PDFs.

## Useful Scripts

- `scripts/find_latest_handoff.py`: locate likely current handoff files.
- `scripts/extract_metrics.py`: extract compact metrics from AFE run CSVs.
- `scripts/make_four_plot_panel.py`: stitch four PNG plots into a 2x2 panel.
- `scripts/candidate_report_check.py`: check a candidate report/run directory
  for expected evidence artifacts before review or handoff.
- `scripts/pseudor_connectivity_audit.py`: extract pseudoR-like instance node
  mappings from netlists for PSUB/DNW/PWELL/A/B connectivity review.

These scripts are helpers, not the source of truth. Read generated reports and
CSV files when the task is high-stakes or when a result looks surprising.
