# Simulation Gates

## Before Spectre

Do not start transistor-level runs until the current phase is clear:

- If metrics are undefined, return to the specification table.
- If architecture is undecided, build an architecture matrix.
- If device/passive feasibility is unknown, build primitive tables first.
- If the limiting mechanism is unknown, build or update a behavioral model.
- If a block is structurally uncertain, run a focused standalone/module gate
  rather than full-chain sweeps.

## Gate Order

For transistor-level work, always run gates in this order unless the user
explicitly asks for a diagnostic shortcut:

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

No AC, noise, or STB claim is valid unless the same candidate has already
passed a clean DC gate without functional ideal elements.

## Module Completion Artifacts

Every completed small module must leave a module-level report and simulation
result images before being promoted to the next integration step.

Minimum module artifacts:

- Short Markdown report with scope, topology, source netlist, testbench,
  PVT/corners, passed/failed gates, metrics, worst corner, risks, and next step.
- DC/operating-point summary table or screenshot.
- AC/gain/bandwidth plot when relevant.
- Noise plot or noise contribution table when relevant.
- STB/loop plot for OTA, CMFB, well-bias, servo, or feedback-loop modules.
- CMRR/PSRR/rejection plot when the module claims rejection behavior.
- Startup/recovery transient plot for reset, slow servo, high-Z, or bias
  modules.
- Connectivity audit image/table for pseudoR/well-bias/netlist rewrites.

Do not promote a block to full-chain just because raw simulator files exist.
The module report should be human-readable and should link the exact images and
CSV/log files used for the decision.

## Tapeout-Candidate Extension

Before a schematic candidate is called final or tapeout-oriented, read
`tapeout-ready-constraints.md` and confirm:

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
- PEX, MC/mismatch, test, trim, calibration, ESD/top-level, and DFM plans exist
  when the candidate is promoted toward tapeout.

## Functional Ideal Audit

Every report should list functional ideal resistor count, functional ideal leak
count, behavioral source count, functional 0 V probe/tie count, ideal current
reference usage, PEX pseudoR count, real MOS return count, and real cap count.
Behavioral CMFB, VCVS blocks, and huge ideal resistors are architecture
exploration aids only; they are not transistor-level candidate evidence.

## Deterministic PVT

Use six corners unless a quick diagnostic is explicitly requested:

- `tt/27C`, `tt/85C`
- `ss/27C`, `ss/85C`
- `ff/27C`, `ff/85C`

Extract and report:

- DC status and power.
- Gain at 300 Hz, 1 kHz, and 10 kHz.
- fHP and fLP.
- Integrated input-referred noise over 300 Hz to 10 kHz.
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

## CMRR and PSRR

- Nominal/symmetric CMRR and PSRR can hit numerical floors or cancellation
  artifacts. Treat them as smoke tests.
- For final plots or literature comparison, use mismatch-aware curves.
- For tapeout-candidate claims, separate ideal schematic, deterministic
  mismatch, and PEX plus MC evidence tiers.
- The preferred deterministic rejection stress is often `CINP +0.1%`; keep
  `CINP +1%` as a stress reference.
- Good differential PSRR does not guarantee quiet output common-mode. Report
  VDD-to-output-CM separately when supply sensitivity matters.
- Useful mismatch stresses include capacitor mismatch from 0.03% to 1%, MOS
  mismatch from 1% to 5%, and parasitic-cap mismatch from 0.5 fF to 5 fF.
- For low-frequency high-pass transition regions, ratio curves may show notches
  or peaks. Focus passband plots on the signal band, usually 300 Hz to 10 kHz.

## Monte-Carlo

- Run MC only after deterministic PVT and mismatch smoke tests are clean.
- Record model section names and variation settings.
- For this process, useful section names may include `mc`, `mc_18`, and related
  mismatch/statistical sections; verify against the local PDK rather than
  guessing.
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
