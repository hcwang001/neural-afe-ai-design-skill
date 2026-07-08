# AFE Workflow

## Purpose

Use this reference for the high-level design loop. The workflow is optimized for
future AFE projects, not for reproducing one historical conversation. It turns
chat history into evidence, then runs a phase-gated design process.

## Phase 0: Context Ingestion

1. Find the newest handoff and relevant older handoffs.
2. Separate facts from decisions:
   - Facts: measured reports, netlists, CSVs, plots, area tables.
   - Decisions: active branch, rejected branches, fallback branches.
   - Lessons: failure mechanisms, modeling blind spots, user constraints.
3. Do not assume the latest branch is optimal. Re-enter the flow at the correct
   phase.

## Phase 1: Specifications And Evidence Targets

Define the target table before any circuit changes:

- Signal band and accepted passband.
- Total gain and gain distribution.
- Input-referred noise, preferred and acceptable.
- Power/channel, preferred and acceptable.
- Area/channel and 256-channel area.
- Input impedance and backend load.
- fHP/fLP, common-mode range, output swing.
- CMRR and PSRR, including mismatch condition.
- Startup/recovery, offset, MC yield, and layout risk.

Classify each target as either a hard must-pass requirement or a preference.
Do not turn preferences such as exact nominal VoutCM, lowest possible power,
smallest cap, or highest loop UGF into hard constraints unless the system
requires them.

Also define evidence level:

- Literature-only.
- Behavioral model.
- Standalone transistor PVT.
- Full-chain deterministic PVT.
- Mismatch-aware deterministic.
- Foundry MC.
- Post-layout/layout-aware.

## Phase 2: Literature And Architecture Shortlist

Build an architecture matrix before transistor-level commitment. Include local
prior branches and external references.

Candidate rows may include:

- Capacitive-feedback LNA plus PGA/VGA.
- Two-stage Miller-compensated LNA.
- Lower-gain stage-1 plus high-Z PGA.
- DC-coupled or servo-based alternatives.
- Direct-conversion or ADC-integrated alternatives.

Columns should include noise, power, area, fHP/fLP feasibility, input impedance,
backend drive, CMFB complexity, pseudoR/well-bias needs, MC/layout risk, and
why the architecture should or should not proceed.

## Phase 3: Primitive Characterization

Before broad circuit sweeps, build tables for:

- gm/Id, gm/gds, ro, noise density, capacitance, and operating region.
- MIM/MOSCAP density and voltage limits.
- rppoly area, parasitic capacitance, resistor noise, and PVT spread.
- pseudoR leakage, fHP impact, terminal mapping, and area.
- Current mirror feasibility and manufacturable current levels.

Use these tables to bound design ranges. Avoid asking Spectre to solve an
unbounded design search.

## Phase 4: Behavioral And System Modeling

Create behavior models before transistor trial-and-error:

- Full-chain gain/noise/loading/bandwidth budget.
- Architecture-level power and area budget.
- Loop models for CMFB, well-bias, servo, and compensation.
- Measured-port models once transistor data exists.

The model must include the suspected limiting mechanism. A chain budget that
omits CMFB offset, plant gain, or headroom cannot validate a CMFB topology.

## Phase 5: Transistor Implementation

Only after phases 1-4 are credible:

1. Implement the smallest block that tests the hypothesis.
2. Run DC first across PVT.
3. Check operating regions, headroom, bias replication, and common-mode.
4. Run AC/noise/rejection/stability only after DC passes.
5. Compare against the behavioral model and update the model when needed.
6. Audit functional ideal elements before promoting any result.
7. Generate a module-level report and result images for each completed block
   before moving to the next block or full-chain integration.

## Phase 6: Full-Chain Integration

Promote a block only when module gates pass. Full-chain runs should answer
system questions, not debug an unknown transistor block.

Full-chain must report power, gain, fHP/fLP, noise, CMRR, PSRR, common-mode,
offset, startup, and backend loading assumptions.

## Phase 7: Variation, Layout, And Reporting

1. Run deterministic mismatch before foundry MC.
2. Run MC only after deterministic gates are sane.
3. Update area with the same topology as the electrical run.
4. Generate final plots and literature comparison rows.
5. Generate a physical-block floorplan suggestion image.
6. Close the branch with the decision template from `decision-rules.md`.
7. Leave a dated handoff with exact files and open risks.

## Historical Lessons To Preserve

- Architecture B was not rejected merely because a behavior model looked bad;
  the transistor-level CMFB plant had extreme sensitivity that the early model
  did not capture.
- Architecture C became stronger after comparing system budgets and backend
  loading rather than forcing a single high-R stage-1 route.
- Standalone CMFB models can under-model the integrated plant. Use measured-port
  or co-design models once integrated transistor data exists.
- Do not continue dense RC or gm sweeps after repeated structural failures.
  Re-express the problem as required port behavior or architecture change.
- Ideal sources, ideal resistors, or ideal VCVS blocks are useful for setting
  requirements, but not final evidence.
- A layout suggestion is not an area treemap. It must express signal flow,
  differential symmetry, common-mode islands, local well-bias placement, and
  excluded simulation proxies.
- If sizing sweeps stop improving the design, freeze the best result as a
  diagnostic reference and open a topology/root-cause branch.
