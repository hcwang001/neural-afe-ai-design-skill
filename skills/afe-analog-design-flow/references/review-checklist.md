# Review Checklist

Use this before installing the skill globally or publishing it.

## Methodology Review

- The flow starts with specifications and literature, not with the latest
  transistor branch.
- Multiple architectures are compared before one is selected.
- Primitive/device characterization appears before broad circuit sweeps.
- Behavioral models are required before expensive transistor iteration.
- The model guidance explicitly warns against omitting the suspected failure
  mechanism.
- DC-first simulation order is preserved.
- Every completed small module has a human-readable simulation report and
  result images before being used as full-chain evidence.
- Functional ideal element audit is required before claims are promoted.
- Branches close with a decision-rules review, not only a metric table.
- Mismatch-aware CMRR/PSRR are required for final claims.
- A final physical-block floorplan suggestion image is generated before
  handoff.

## Project-Specific Leakage Review

- No PDK model files are included.
- No raw PEX netlists are included unless explicitly cleared.
- No private PDFs or copied paper content are included.
- No PSF/raw Spectre databases are included.
- Absolute local paths appear only as examples or are removed before GitHub.
- Current INT090 numbers are clearly marked as an example/reference, not as a
  universal skill assumption.

## Technical Completeness Review

- Literature extraction covers measurement bands and included blocks.
- Architecture matrix includes noise, power, area, gain, bandwidth, input
  impedance, backend loading, CMRR/PSRR, offset/startup, and layout risk.
- Device tables include gm/Id, gm/gds, capacitance, noise, leakage, area, and
  operating-region checks.
- Behavioral modeling includes full-chain budget, loop/plant model, and
  measured-port update path.
- Handoff template captures current phase, specs, architecture state, models,
  latest gates, metrics, and next step.
- Handoff links module-level reports and module-level result images for each
  completed block.
- Handoff captures hard-versus-preference metrics, worst corner, limiting
  mechanism, functional ideal elements, and whether further sizing sweeps still
  have expected value.
- Floorplan image excludes simulation-only proxies unless they are explicitly
  labeled, and it shows differential symmetry, signal flow, common-mode islands,
  pseudoR/well-bias locality, and layout caveats.
- `scripts/candidate_report_check.py` has been run, or the equivalent evidence
  checklist has been manually reviewed.

## Tapeout Readiness Review

- Device groups report W/L/fingers, device type, voltage domain, current,
  gm/Id, Vov, VDS/VDSAT, region, noise contribution, mismatch criticality,
  layout matching requirement, chosen-size rationale, and risk.
- No analog-critical path relies on unjustified minimum-size MOS, extreme W/L,
  ultra-low current, or leakage-defined behavior.
- Current mirrors, bias replicas, CMFB bias branches, and well-bias drivers
  have credible long-channel/matching/headroom choices.
- Device reliability is audited for `VGS`, `VGD`, `VDS`, `VGB`, `VDB`, `VSB`,
  body diode bias, and thin/thick-oxide domains, including startup/reset.
- Precision capacitors below 50 fF have unit-cap, parasitic, mismatch, PEX gain
  error, and CMRR-impact notes.
- Gain-setting capacitor ratios use matched arrays when possible; large
  compensation capacitors include area and parasitic justification.
- Every high-Z node is classified and has DC, startup, reset-recovery,
  leakage, parasitic, noise, CMRR/PSRR, and shielding answers.
- Bias/reference sources are realizable or documented as top-level plans;
  ideal current sources are not treated as final evidence.
- PSRR is decomposed by supply/reference path, including output common-mode
  ripple where relevant.
- Startup, reset, MUX/ADC kickback, gain-code switching, standby-active
  switching, and slow-servo recovery are covered before promotion.
- PEX path, parasitic stress tests, MC/mismatch plan, test observability,
  trim/calibration plan, ESD/pad/top-level interface plan, and DFM risks are
  captured before calling a candidate tapeout-oriented.
- pseudoR/well-bias netlist rewrites have a connectivity audit. Use
  `scripts/pseudor_connectivity_audit.py` as a first-pass extractor when a
  sanitized netlist is available.

## Open Items

- Merge any missing lessons from old chats not already represented by the
  handoff documents.
- Decide whether the GitHub repo should include only the skill folder or a
  wrapper README and `.gitignore`.
- Forward-test the skill with `forward-test-prompts.md` in fresh threads before
  publishing.
