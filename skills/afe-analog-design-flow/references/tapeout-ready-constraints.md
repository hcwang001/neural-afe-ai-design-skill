# Layout, Post-Layout, And Tapeout Technical Constraints

Use this reference when preparing G7 layout-ready, G8 PEX, G9 post-layout
signoff, or G10 release artifacts. It contains technical constraints, not gate
authorization. Codex may identify gaps and prepare draft evidence but may not
write `approved`, complete an independent review, or authorize release.

Project-specific device rules, voltage domains, corners, capacitance thresholds,
and layout limits must come from the approved specification/PDK overlay. Numeric
values retained below are engineering heuristics or historical examples unless
the project explicitly adopts them as controlling requirements.

## Core Principle

Do not nominate a G7 candidate solely because schematic PVT is clean. A
layout-ready candidate must be physically realizable, layout-aware, reliability-clean,
mismatch-aware, startup-safe, and free of functional ideal aids. When more
power or sizing no longer helps, stop sweeping and identify the dominant
physical mechanism.

## G7 Layout-Ready Technical Criteria

A schematic candidate may be nominated for G7 review only if:

1. DC is clean across required corners without functional ideal elements.
2. Every MOS device passes operating-region and reliability checks.
3. Gain, bandwidth, noise, and power meet spec across PVT.
4. Stability uses the correct differential, CMFB, and slow-loop probes.
5. Startup, reset, and recovery transients pass.
6. CMRR and PSRR are mismatch-aware, not nominal-only.
7. Noise contributors are decomposed.
8. Every high-Z node has explicit DC, startup, leakage, and recovery paths.
9. Every bias/reference has a realizable source or top-level plan.
10. Capacitors, resistors, and pseudo-resistors have layout-feasible
    implementations.
11. Area and power per channel are reported.
12. Parasitic sensitivity is checked before layout.
13. A PEX implementation and verification path is defined.
14. Required schematic MC and mismatch evidence is already current.
15. Test, trim, calibration, ESD, and interface implementations are defined and
    traceable to G7 artifacts.

This list cannot satisfy G8, G9, or G10. G8 requires actual layout/extraction
identity and DRC/LVS/PEX artifacts. G9 requires extracted re-verification and
post-layout MC. G10 requires the immutable release package and organization-
defined human release authorization.

## Device Sizing Rules

Do not use minimum-length or minimum-width MOS devices in analog-critical paths
unless explicitly justified by speed, capacitance, or switch on-resistance.
Analog-critical paths include input pairs, current mirrors, CMFB input pairs,
CMFB actuators, bias replicas, pseudoR well-bias drivers, output loads, and
PGA/VGA core devices.

For current mirrors, bias references, replica devices, and CMFB bias branches:

- Prefer longer-than-minimum channel length.
- Historical analog heuristics often start current mirrors above minimum
  length. Exact ratios such as `2x-5x Lmin` or `>=4x Lmin` are not universal
  gates and require project/PDK justification.
- Report VDS matching and saturation margin.
- Avoid extreme weak inversion unless mismatch and leakage are verified.
- Choose input/noise device `L` from the noise, gm, ro, Cin, and area tradeoff,
  not from one metric alone.

Reject candidates that rely on extreme W/L, ultra-low current, or
leakage-dominated behavior unless PDK model validity is confirmed, layout area
is estimated, mismatch/MC passes, and parasitic sensitivity is checked.

Every MOS device group report should include:

```text
Device group:
Function:
W/L/fingers:
Device type:
Voltage domain:
Bias current:
gm/Id:
Vov:
VDS:
VDSAT:
region:
noise contribution:
mismatch criticality:
layout matching requirement:
reason for chosen size:
risk:
```

Every size choice must state the tradeoff among noise, gain, headroom,
capacitance, mismatch, layout area, and stability.

## Leakage-Dominated Primitive Rules

Any device whose function depends on fA-pA leakage is a high-risk primitive.
Examples include pseudo-resistors, MOS-off returns, subthreshold active-R
devices, well-bias leakage compensation, and ultra-weak bleed paths.

Do not sign off leakage-dominated devices with nominal PVT only. Verify
temperature sweep, FF/SS leakage, well/DNW/PSUB leakage, mismatch, startup,
long transient, noise contribution, and PEX sensitivity.

## Reliability And Voltage-Domain Rules

Every promoted candidate must pass a device reliability audit:

- No MOS terminal voltage exceeds PDK recommended operating limits.
- No unintended source/drain/well/body junction is forward biased.
- No cross-domain thin-oxide overstress occurs.
- No startup, reset, or switching transient overstress occurs.

Audit `VGS`, `VGD`, `VDS`, `VGB`, `VDB`, `VSB`, body diode bias, and every
thick/thin-oxide domain in the approved project overlay. Historical 1.2 V,
1.8 V, and 2.5 V domains are examples only. Include DNW/PWELL well-bias,
pseudoR body bias, MUX/ADC, PMU, pad, and top-level interfaces.

Reliability must be checked during power-up ramp, reset asserted, reset
release, standby/active switching, MUX switching, gain-code switching, and
stimulation/artifact recovery when applicable.

## Capacitor And Resistor Layout Rules

Any precision capacitor near the project's routing/parasitic floor is a
layout-risk primitive. A historical screening threshold is 50 fF, but the
approved PDK/layout overlay controls. The device must report
unit-cap implementation, routing parasitic estimate, top/bottom plate
parasitic, mismatch sensitivity, PEX gain error, and CMRR impact.

For gain-setting MIM capacitors:

- Use unit-cap arrays when possible.
- Use common-centroid or interdigitated layout when mismatch matters.
- Add dummy units and maintain identical surroundings.
- Route top and bottom plates symmetrically.
- Avoid asymmetric overlap over active MOS.
- Include PEX before final CMRR/PSRR claims.

`Cin/Cf` ratio should use a matched unit-cap array whenever practical. Do not
treat an isolated 10 fF schematic capacitor as final layout evidence.

Explicit compensation capacitance must be area-budgeted. The following bands
are historical screening examples, not universal gate thresholds:

- `<500 fF`: usually acceptable, still check parasitics when precision matters.
- `0.5-2 pF`: acceptable with area note.
- `2-10 pF`: requires area and parasitic justification.
- `10-20 pF`: high-risk.
- `>20 pF`: topology review required.

The project overlay must define report and red-flag thresholds for per-channel
capacitance. Historical examples used 1 pF for mandatory area reporting and
5 pF as a layout-risk trigger.

## Symmetry, Matching, CMRR, And PSRR

For fully differential paths, left/right symmetry is a signoff requirement, not
a preference. Match input capacitors, feedback capacitors, pseudoR paths,
well-bias drivers, input pairs, loads, CMFB sense pairs, CMFB actuators, bias
mirror branches, output routing, MUX input routing, and shielding.

Separate rejection evidence into three tiers:

1. Ideal symmetric schematic result: upper bound only.
2. Deterministic mismatch result: design gate.
3. PEX plus Monte-Carlo result: signoff candidate.

Do not promote CMRR/PSRR based on nominal symmetric simulation. A CMRR claim
without capacitor mismatch and PEX is not a signoff claim.

PSRR must be decomposed by supply/reference path, including analog VDD, bias
reference VDD, CMFB reference VDD, pseudoR well-bias VDD, VOCM/VCM reference,
stage-2/MUX supply, and ADC sampling supply when present. Report at least
VDD-to-VoutDM, VDD-to-VoutCM, VDD-to-bias-node, VDD-to-high-Z-control-node,
and VDD-to-pseudoR-well-node paths. Good differential PSRR does not imply safe
output common-mode ripple.

## PEX And Parasitic Stress Rules

A transistor-level candidate cannot satisfy G8/G9 without the defined PEX path:

1. Schematic clean gate.
2. Pre-layout PVT.
3. Estimated parasitic stress.
4. Layout.
5. LVS/DRC clean.
6. RC extraction.
7. Post-layout DC, AC, noise, STB, and transient.
8. Post-layout CMRR/PSRR with mismatch.

Before layout, every high-Z node must receive a parasitic sensitivity check.
Pre-layout stress values must be project-approved. Historical examples include:

- Input parasitic mismatch: 0.5 fF, 1 fF, 2 fF, 5 fF.
- Output load capacitance: 25 fF, 50 fF, 100 fF, 200 fF.
- Control-node capacitance: +10 fF, +50 fF, +100 fF.
- Bias-node capacitance: +50 fF, +200 fF.
- Routing resistance: 10 Ohm, 100 Ohm, 1 kOhm where relevant.

## High-Impedance Node Rules

Classify every high-impedance node as one of:

- Signal high-Z.
- Bias high-Z.
- CMFB control high-Z.
- pseudoR well high-Z.
- Storage or hold node.
- Startup-only floating node.

For each high-Z node, answer:

1. What is the DC path?
2. How is startup defined?
3. How does it recover after reset?
4. What leakage paths exist?
5. What is the expected post-PEX parasitic capacitance?
6. Does it affect noise?
7. Does it affect CMRR/PSRR?
8. Does it need shielding, guard ring, or isolation?

No floating or leakage-defined node can be accepted unless leakage, startup,
noise, PVT, and recovery behavior are explicitly verified.

## Bias And Reference Rules

Ideal current sources are allowed only in early exploration. Before tapeout
promotion, each bias/reference must have a realizable source or documented
top-level bias plan.

For every bias/reference, report source, current value, mirror ratio, headroom,
temperature dependence, supply sensitivity, noise contribution, startup state,
enable/disable behavior, and layout matching. Include VCM/VOCM, CMFB bias,
pseudoR well-bias, PGA bias, MUX/ADC references, and any bandgap/LDO-derived
references.

## Stability, Startup, And Recovery Rules

Use `diffstbprobe` or an equivalent fully differential method for differential
and CMFB loop claims. A single-ended `iprobe` is not a substitute for
fully-differential or common-mode loop validation.

Validate differential signal loops, CMFB loops, well-bias slow loops,
bias/reference loops, LDO/reference loops if present, and sampled/standby
recovery loops separately.

If a loop uses a slow servo, report both low-frequency tracking bandwidth and
signal-band isolation. A slow servo is not signed off by AC bandwidth only; it
must pass startup and recovery.

Transient promotion checks should include power-up, reset assert/release, input
common-mode step, large differential input, common-mode pulse, MUX/ADC
kickback, gain-code switching, standby-active switching, and pseudoR/well-bias
recovery. Report settling time, overshoot, final error, wrong-state risk,
device stress, and baseline drift.

## Multi-Channel, Test, Trim, And Calibration Rules

Every per-channel circuit addition must report area per channel, power per
channel, number of bias/reference wires, number of trim bits, routing overhead,
shared versus local implementation, and test observability.

If a metric is mismatch-limited, propose one of:

- Layout-only strategy.
- Trim strategy.
- Digital calibration strategy.
- Relaxed spec justification.

Common trim candidates include `Cin/Cf` ratio, CMRR balance, well-bias offset,
pseudoR HPF corner, PGA gain, VOCM, bias current, and ADC offset. Each trim
proposal must report range, step, bits, area, switch parasitic, noise impact,
calibration method, and whether it is per-channel or global.

## ESD, Pad, Top-Level, And DFM Rules

Any external electrode/input interface must include an ESD/top-level plan.
For neural AFE inputs, include input ESD capacitance, ESD leakage, protection
clamp leakage, stimulation artifact tolerance, input reset path, electrode DC
offset range, and input common-mode range.

Input capacitance budget must include ESD, pad, routing, MUX, and package
parasitics, not only MOS `Cgg`.

At G7-G10 as assigned by policy, account for DRC, LVS, antenna, metal density, slotting, well
density, dummy fill impact, EM/IR for shared bias/reference lines, latch-up
spacing, guard rings, and substrate isolation. Post-fill extraction must be
considered for high-Z and small-cap nodes.

None of these technical checks grants G10 release. The release package remains
human-controlled and must reference an effective G9 approval and current
digests for all released views.
