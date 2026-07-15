# Plots And Reporting

Plots and reports are derived views, not gate state. Every promoted claim must
reference a current evidence ID and parsed controlling metric. Bands, corner
labels, and plot frequencies shown below are historical neural-AFE examples;
the approved project overlay controls.

## Module-Level Reports

After every small module design is completed, generate a human-readable module
report and result images before moving to the next block or full-chain
integration.

Module reports should include:

- Module name, run ID, topology, source netlist, and testbench.
- Spec target and evidence level.
- DC/PVT status, operating regions, current/power, common-mode, and headroom.
- Relevant AC/gain/bandwidth, noise, STB, rejection, startup/recovery, or
  connectivity results.
- Image paths and CSV/log paths used for each claim.
- Worst corner, limiting mechanism, open risks, and next action.

Module images should be generated for the behavior the module is supposed to
own. Examples:

- Stage-1 LNA: gain, input-referred noise, input impedance, CMRR/PSRR if
  claimed, startup/reset if relevant.
- Stage-2/PGA: gain/bandwidth, output common-mode, noise contribution,
  backend-load response, CMFB/STB if applicable.
- CMFB: loop gain/phase, VoutCM regulation, startup/recovery.
- pseudoR/well-bias: fHP impact, PWELL/DNW tracking, leakage/PVT, startup, and
  connectivity audit table.
- Bias/reference: current versus PVT, headroom, startup, PSRR/noise if
  relevant.

Raw simulator output alone is not a module report.

## Required Final Plots

For a comparison-quality full-chain candidate, generate:

1. Gain-bandwidth curve.
2. Input-referred noise density versus frequency.
3. CMRR versus frequency using mismatch-aware curves.
4. VDD PSRR versus frequency using mismatch-aware curves.

Use a shaded signal band, usually 300 Hz to 10 kHz. If CMRR/PSRR have
low-frequency high-pass-transition artifacts, use a passband-focused x-axis for
the final plot and explain why.

## Plot Rules

- Use all deterministic PVT corners in one figure when readable.
- Label project-defined conditions consistently. `TT27`, `TT85`, `SS27`,
  `SS85`, `FF27`, and `FF85` are legacy example labels only.
- Do not plot nominal/symmetric CMRR/PSRR as final rejection when mismatch-aware
  data exists.
- Keep source CSV paths in the report.
- Use `scripts/make_four_plot_panel.py` to create a 2x2 overview image.
- Use `scripts/candidate_report_check.py` only to discover candidate-like files.
  Its hits are not metric evaluation, evidence, readiness, or gate state.
- Generate the overall floorplan suggestion image separately; do not merge it
  into the four electrical performance plots.

## Report Sections

Good reports include:

- Scope and topology.
- Source netlist and generated wrappers.
- Connectivity audit for pseudoR/well-bias edits.
- Deterministic PVT summary.
- Mismatch-aware rejection summary.
- MC status when available.
- Generated data paths.
- Final plot paths and floorplan image path.
- Decision and next step.

## Curve Sanity Checks

Before sending plots:

- Gain should have the expected high-pass and low-pass behavior.
- Noise should not be referenced through the wrong gain.
- CMRR/PSRR should be smooth in the passband.
- Any spikes/notches should be explained as transition/cancellation artifacts or
  investigated before use.
