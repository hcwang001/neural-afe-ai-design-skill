# Simulation Gates

## Governance Meaning

These are simulation sequencing rules, not lifecycle authorization gates. A
result becomes promotion evidence only through a current evidence manifest and
the G5-G9 mandatory-artifact policy. "DC passed" describes an analysis result;
it does not change project state or authorize the next lifecycle gate.

A user-requested diagnostic shortcut must be recorded with
`exploratory_only: true` and `promotion_eligible: false`. It cannot later be
used for promotion without formal revalidation against the approved baseline.

## Before Spectre

Do not start transistor-level runs until the current phase is clear:

- If metrics are undefined, return to the specification table.
- If architecture is undecided, build an architecture matrix.
- If device/passive feasibility is unknown, build primitive tables first.
- If the limiting mechanism is unknown, build or update a behavioral model.
- If a block is structurally uncertain, run a focused standalone/module gate
  rather than full-chain sweeps.

## Gate Order

For transistor-level work, run checks in this order unless the user explicitly
asks for a non-promotion diagnostic shortcut:

1. DC operating point.
2. AC, gain, and bandwidth only for DC-passing cases.
3. Noise.
4. `diffstbprobe` or equivalent stability check.
5. Startup/recovery transient.
6. CMRR and PSRR with deterministic mismatch.
7. Deterministic mismatch smoke.
8. Foundry Monte-Carlo.
9. Reliability, high-Z-node, and layout-feasibility audit.
10. Post-layout extraction when available.

No AC, noise, or STB claim is valid unless the same immutable candidate revision
has current clean-DC evidence without functional ideal elements.

## Module Completion Artifacts

Every completed small module must leave a module-level report and simulation
result images before it can be nominated as G5/G6 evidence.

Minimum module artifacts:

- Short Markdown report with scope, topology, source netlist, testbench,
  PVT/corners, satisfied/failed simulation checks, metrics, worst condition,
  risks, and next step.
- DC/operating-point summary table or screenshot.
- AC/gain/bandwidth plot when relevant.
- Noise plot or noise contribution table when relevant.
- STB/loop plot for OTA, CMFB, well-bias, servo, or feedback-loop modules.
- CMRR/PSRR/rejection plot when the module claims rejection behavior.
- Startup/recovery transient plot for reset, slow servo, high-Z, or bias
  modules.
- Connectivity audit image/table for pseudoR/well-bias/netlist rewrites.

Do not nominate a block for full-chain use just because raw simulator files exist.
The module report should be human-readable and should link the exact images and
CSV/log files used for the decision.

## Layout-Ready And Later-Gate Extension

Before an integrated schematic candidate is nominated for G7 layout-ready
review, read `tapeout-ready-constraints.md` and confirm:

- Device sizing is manufacturable; no analog-critical path relies on
  unjustified minimum-size MOS, extreme W/L, ultra-low current, or unverified
  leakage behavior.
- Every MOS voltage domain and terminal stress is checked, including startup,
  reset, switching, and well/body bias transients.
- Precision capacitors below 50 fF, large compensation capacitors, resistors,
  pseudo-resistors, and MOSCAPs have layout-feasible implementations.
- Fully differential symmetry and matching are part of the signoff plan.
- High-Z nodes have explicit DC, startup, leakage, parasitic, and recovery
  answers.
- Bias/reference sources are realizable or have a documented top-level plan.
- MC/mismatch evidence is current, and test, trim, calibration, ESD/top-level,
  PEX, and DFM artifacts meet the mandatory G7 policy.

G7 is not PEX or tapeout release. Actual PEX evidence is mandatory at G8/G9,
extracted verification at G9, and the release package and human release
authorization at G10.

## Functional Ideal Audit

Every report should list functional ideal resistor count, functional ideal leak
count, behavioral source count, functional 0 V probe/tie count, ideal current
reference usage, PEX pseudoR count, real MOS return count, and real cap count.
Behavioral CMFB, VCVS blocks, and huge ideal resistors are architecture
exploration aids only; they are not transistor-level candidate evidence.

## Deterministic PVT

Use the conditions approved by the project specification and PDK. The following
six-point set is a legacy neural-AFE example, not a universal gate definition:

- `tt/27C`, `tt/85C`
- `ss/27C`, `ss/85C`
- `ff/27C`, `ff/85C`

Extract and report:

- DC status and power.
- Gain at project-defined check frequencies (legacy example: 300 Hz, 1 kHz,
  and 10 kHz).
- fHP and fLP.
- Integrated input-referred noise over the approved signal band (legacy
  example: 300 Hz to 10 kHz).
- Noise density near 1 kHz when useful.
- CMRR and VDD PSRR relative to differential gain.
- Output common-mode and differential offset.

## Sweep Policy

- Sweep only parameters tied to a hypothesis from the model or primitive table.
- Keep sweep grids small enough to review.
- Include a decision table after each sweep.
- Stop if all candidates fail for the same structural reason; update the model
  or architecture instead of widening the sweep.
- Do not run AC/noise on candidates that fail DC or basic operating-region
  checks.
- If two consecutive sweeps improve the target by less than the design margin
  while increasing power or area, freeze the best result as a diagnostic
  reference and open a topology/root-cause branch.

## Physical Compensation Gate

Use this simulation check before nominating any block whose stability or
bandwidth depends on an ideal compensation branch:

1. Run a diagnostic requirement scan: no branch, capacitor only, resistor only,
   and a small set of RC candidates.
2. Co-sweep only the device ratios tied to the measured plant mechanism.
3. Verify a finalist across deterministic PVT with margin, not just at the
   nominal or exact pass/fail threshold.
4. Replace ideal passives with PDK resistor/capacitor devices and the correct
   process/model sections. Use distributed resistor segments when appropriate.
5. Rerun DC, exact differential/CMFB STB, AC/noise, and common-mode disturbance
   recovery.
6. Export and independently run a clean nominal/module deck that does not
   depend on mutable public snapshots.

The report must compare ideal and physical values, list passive PVT ranges,
distributed parasitic capacitance, area, and remaining mismatch/PEX risks.
Never nominate a physical-RC result from an ideal-area proxy alone.

## CMRR and PSRR

- Nominal/symmetric CMRR and PSRR can hit numerical floors or cancellation
  artifacts. Treat them as smoke tests.
- For final plots or literature comparison, use mismatch-aware curves.
- Separate ideal schematic diagnostics, deterministic mismatch, and PEX plus MC
  evidence tiers. Lifecycle policy decides which tier is mandatory at G6-G9.
- Deterministic rejection stresses must come from the project overlay; legacy
  values such as `CINP +0.1%` and `CINP +1%` are examples only.
- Good differential PSRR does not guarantee quiet output common-mode. Report
  VDD-to-output-CM separately when supply sensitivity matters.
- Capacitor, MOS, and parasitic-cap mismatch stresses must come from the
  approved project/PDK plan; historical ranges are examples only.
- For low-frequency high-pass transition regions, ratio curves may show notches
  or peaks. Focus final plots on the project-defined passband.

## Monte-Carlo

- Run MC only after deterministic PVT and mismatch smoke tests are clean.
- Record model section names and variation settings.
- Statistical section names are project/PDK overlay data. Historical names such
  as `mc` or `mc_18` must never be inferred for a new project.
- Report sample count, parsed count, failures, min/max/mean/sigma, and worst
  samples.

## Stop Conditions

Stop and analyze before more simulation when:

- A low-gain or headroom outlier appears.
- fHP/fLP shifts by orders of magnitude.
- CMRR/PSRR curves show discontinuous spikes in passband.
- PseudoR terminal or well-bias connectivity is uncertain.
- Area basis changes without a clear delta table.
- The limiting mechanism is unknown but sweep count is growing.
- A candidate only passes by using a layout-risk primitive, unverified
  leakage-defined node, ideal bias/reference, or device sizing that cannot be
  defended for tapeout.
