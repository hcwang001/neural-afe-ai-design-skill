# AFE Decision Rules

## Governance Boundary

This file governs technical recommendations: continue, stop, change topology,
or nominate an immutable candidate for review. It does not authorize a gate.
Words such as promote, freeze, final, close, or pass in historical material are
technical branch dispositions only. Lifecycle state is controlled by the
machine policy, current evidence, independent review, gatekeeper evaluation,
and a separate human approval record.

Codex may write a proposal, analysis result, candidate nomination, or draft
decision record. It must not write `approved`, complete an independent review,
approve a waiver, or substitute a branch decision for G0-G10 closure.

All numeric values in this reference are explicitly historical examples, not
default criteria. Only the instantiated requirements traceability and approved
PDK/project overlay may supply controlling thresholds.

Use this reference whenever a design branch is being planned, evaluated,
promoted, paused, or rejected. The goal is to prevent blind simulation and to
turn each branch into evidence.

## Core Rule

Do not optimize a metric until the dominant mechanism is identified. Do not
nominate a transistor candidate unless the applicable simulation checks are
satisfied without functional ideal aids. Do not keep sweeping device sizes when
the failure pattern indicates
a topology, leakage, matching, or reference-path limitation.

For layout-oriented work, do not nominate a G7 candidate solely because
schematic PVT is clean. The candidate must be physically realizable,
reliability-clean, mismatch-aware, startup-safe, layout-aware, and backed by a
PEX/test/trim plan when those risks apply. Read
`tapeout-ready-constraints.md` before G7 review. G8 PEX, G9 post-layout, and G10
release remain separate human-controlled gates.

## Hard Metrics Versus Preference Metrics

Separate must-pass requirements from preferences before changing a circuit.

Hard metrics include:

- DC convergence across required corners.
- Correct operating regions and headroom.
- No functional ideal resistor, ideal leak, or behavioral source in the path
  being claimed as real.
- Input impedance and backend loading within system limits.
- Output not rail-stuck and common-mode inside the valid corridor.
- Stability margin passes the chosen gate.
- Noise, CMRR, and PSRR meet the system requirement.

Preference metrics include:

- VoutCM exactly equal to a nominal value such as 0.600 V.
- Lowest power among otherwise close candidates.
- Smallest capacitor or smallest area.
- Higher loop UGF than needed.
- A circuit that looks simpler but has weaker evidence.

Write output common-mode requirements as a corridor, not a single exact number:
the allowed VoutCM range is defined by current-stage headroom, next-stage input
range, gain code, load, PVT, and transient recovery.

## DC-First Rule

Run transistor simulation checks in this order unless doing an explicitly
labeled `exploratory_only` diagnostic shortcut:

1. DC operating point.
2. AC, gain, and bandwidth.
3. Noise.
4. Stability, preferably with `diffstbprobe` or an equivalent differential
   loop method.
5. Transient startup and recovery.
6. CMRR and PSRR with deterministic mismatch.
7. PVT plus Monte-Carlo.
8. Post-layout extraction.

No AC, noise, or STB claim is valid unless the same immutable candidate has
current clean-DC evidence without functional ideal elements.

## Functional Ideal Element Audit

Every candidate report should list:

- Functional ideal resistor count.
- Functional ideal leak count.
- Behavioral source count.
- Functional 0 V probe/tie count.
- Ideal current reference usage.
- PEX pseudoR count.
- Real MOS return count.
- Real capacitor count.

Interpretation rules:

- An ideal current reference feeding a diode-connected MOS mirror is acceptable
    for early exploration, but not promotion evidence at G5 or later.
- Functional 250 Mohm, 1 Tohm, or similar huge ideal resistors are red flags.
- Behavioral CMFB or VCVS blocks are architecture exploration only, not a
  G5-or-later transistor evidence.
- A 0 V probe or tie is allowed for measurement only; it is not allowed in a
  functional path being claimed as real.

## Stop Blind Sizing Sweeps

Stop sweeping W/L/current and open a root-cause or topology branch when:

- Multiple W/L/current sweeps improve the target by only a few degrees or a few
  percent.
- The same worst corner remains fixed.
- Added current only increases power and does not improve noise, CMRR, or PSRR.
- A compensation capacitor must grow from small values to large values before
  the circuit stabilizes.
- A high-impedance control node repeatedly creates a bad pole.
- pseudoR series count does not scale fHP as expected.

If two consecutive sweeps improve the target metric by less than the design
margin while increasing power or area, freeze the best candidate as a
diagnostic reference and open a topology/root-cause branch.

## CMFB Must Be Co-Designed With The Core

For any fully differential LNA, PGA, or OTA, characterize the common-mode plant:

- Actuator control node to VoutCM gain and phase.
- Output common-mode impedance.
- Control-node impedance.
- CMFB sensing-node pole.
- Actuator gm.
- Differential-path contamination.

Prefer:

- True common-mode sensing.
- Low-Z or buffered control node.
- Fixed main load plus small common-mode correction branch.
- Replica-centered dual actuator when it reduces sensitivity.
- Small correction gm.
- Meet the project-defined phase-margin requirement across required conditions,
  with physically realizable compensation.

Avoid:

- One high-Z gate node controlling the entire main load.
- Per-side fast servos that respond to differential signal.
- Huge compensation cap as the primary solution.
- Wideband followers where a slow servo is required.

## Compensation And Physical-Passive Promotion Rule

Classify every compensation component by mechanism before changing its value:

- DC blocking or bias isolation.
- Pole placement.
- Phase-lead zero placement.
- Damping or output-impedance shaping.
- Leakage or startup path.

Equal `R*C` products are not equivalent when the resistor creates a lead zero
or the capacitor blocks DC coupling. Diagnose a compensation branch with a
small, interpretable set such as no branch, capacitor only, resistor only, and
compact RC. Run DC before stability and stop combinations that violate biasing.

Co-design compensation with the few transistor ratios that directly set plant
gain, actuator gm, or output/control-node impedance. Do not nominate a candidate
that merely touches the phase-margin threshold; retain enough schematic margin
for passive spread and extraction.

Before G5 block-candidate nomination:

1. Replace ideal R/C with the intended PDK devices and verified model sections.
2. Model a multi-megaohm resistor as a distributed structure when its body or
   routing capacitance is comparable to the explicit compensation capacitor.
3. Record PVT ranges for resistance, capacitance, parasitics, noise, voltage
   coefficient, and area.
4. Rerun exact integrated DC, differential/CMFB STB, AC/noise, and disturbance
   recovery with that physical branch.
5. Create a content-addressed module candidate only after these checks are
   satisfied. This does not close G5.

If several independent no-RC sizing strategies all pass DC but fail with the
same structural phase-margin pattern, close that topology branch. Reopen it
only with a changed loop architecture or new mechanism-level evidence, not a
wider sizing sweep.

## Keep Bandwidths Separate

Always separate:

1. Final neural signal bandwidth.
2. Stage closed-loop differential bandwidth.
3. CMFB loop crossover.
4. pseudoR or HPF cutoff.
5. Interstage and ADC settling bandwidth.

Stage differential bandwidth may be much higher than the final neural band if
later filtering defines the final bandwidth. CMFB UGF only needs enough
bandwidth for common-mode settling and recovery; do not push it high unless
transient evidence requires it. Judge pseudoR behavior by fHP and
low-frequency noise, not by nominal resistance alone.

## pseudoR And Well-Bias Rules

pseudoR series count is not valid unless fHP scales as expected. If 1x, 2x,
and 3x series give almost identical fHP, the dominant path is probably not
A-B channel resistance; investigate endpoint, well, DNW, or PSUB leakage.

DNW/PWELL well-bias is usually a slow leakage-compensation servo, not a
wideband follower.

Historical first-pass examples follow. The approved project/PDK overlay must
replace them before they control a design:

- PWELL to DNW tracking bandwidth: 1-10 Hz nominal.
- Acceptable first-pass range: 1-100 Hz.
- Avoid >= 1 kHz unless proven harmless.
- Systematic tracking offset preferably <= 0.3-0.5 mV.
- DNW output should be low impedance enough in the signal band.
- Use independent DNW/PWELL per pseudoR segment when series scaling is being
  verified.

Do not build a wideband unity follower from PWELL to DNW by default. Do not
share DNW/PWELL across pseudoR series cells if leakage scaling is under test.
Do not connect a naked high-Z OTA output directly to DNW.

## Noise Optimization Requires Contribution Decomposition

Before increasing current, identify the dominant noise contributor:

- Input pair.
- Output load.
- PMOS assist path.
- pseudoR.
- CMFB.
- Bias/reference.
- Stage-2 contribution.
- ADC kickback or backend path.

If current increase does not reduce the dominant noise contributor, stop
increasing current.

Each noise report should list input pair noise, output load noise, PMOS assist
noise when relevant, pseudoR noise, CMFB noise, bias/reference noise, stage-2
contribution, and total-chain input-referred noise.

Useful diagnostics include noiseless pseudoR controls, noiseless output-load
controls, ideal-resistor replacement, stage-only versus full-chain comparison,
and corner-specific separate-noise decomposition.

For a series or distributed feedback network, preserve contributor position.
If the input-adjacent cell couples more strongly than upstream cells, test
position-aware sizing before scaling every local driver equally. Include local
well-bias amplifiers and servos as explicit contributor categories.

When a pseudoR/feedback topology change lowers signal gain through PEX
capacitance, compare these recovery options together:

- Increase Cin if input impedance and area remain inside limits.
- Increase a physically safe Cf ratio element only if the desired gain allows
  it.
- Change the feedback topology or cell count.
- Reject the route if gain recovery erases its area/noise advantage.

Do not reduce an already parasitic-dominated feedback capacitor solely to
restore nominal gain.

## CMRR And PSRR Must Be Mismatch-Aware

Nominal symmetric CMRR/PSRR is an upper bound only. Design decisions must use
deterministic mismatch first and later PDK Monte-Carlo.

Historical deterministic stress examples follow. The approved project/PDK
overlay controls actual values:

- Capacitor mismatch: 0.03%, 0.05%, 0.1%, 0.3%, 1%.
- MOS mismatch: 1%, 2%, 5%.
- Parasitic capacitance mismatch: 0.5 fF, 1 fF, 2 fF, 5 fF.

Decompose PSRR paths when supply sensitivity matters:

- VDD to VoutDM.
- VDD to VoutCM.
- VDD to bias nodes.
- VDD to CMFB control node.
- VDD to pseudoR well-bias.
- VDD to VOCM/VCM reference.

Good differential PSRR does not guarantee quiet output common-mode. Report
VDD-to-output-CM separately.

## Recovery Deadlines Must Match The High-Pass Pole

Do not apply an arbitrary millisecond recovery gate to a signal path whose
intentional pseudoR/high-pass time constant is tens or hundreds of
milliseconds.

Separate two claims:

- Natural recovery: characterize the tail against fHP over a physically long
  enough window.
- Assisted recovery: if the product uses blanking, reset, or artifact
  detection, exercise the real reset MOS/control sequence and gate that path.

A slow natural tail is not automatically loop instability. Conversely, a
reset-assisted pass creates a top-level requirement for reset timing,
distribution, and blanking control; record it in the interface contract.

## Freeze Bias Interfaces, Not Hidden Ideal Sources

Before exporting a promoted block:

1. Move ideal current/voltage sources out of the claimed silicon core.
2. Expose the exact bias nodes or current-injection ports used by the validated
   circuit.
3. Keep a separate reproduction harness with the old ideal references.
4. Rerun numerical regression across the required corners.
5. Record which master reference/mirror tree remains to be designed.

Do not redesign the bias mirror silently during netlist cleanup. Interface
cleanup should first preserve the validated electrical operating point.

## Gain Decisions Are Not Noise Decisions

Increasing total gain reduces ADC quantization impact, but it does not improve
analog input-referred SNR once ADC noise is already below analog noise.

Choose gain by checking:

1. Input signal range.
2. Maximum artifact and swing.
3. ADC full-scale and LSB.
4. Input-referred analog noise.
5. Stage output swing.
6. Gain-code coverage.

A legacy neural-AFE starting point was around 40 dB total gain with roughly
30-50 dB programmable range. It is not a universal requirement. Do not increase
stage-1 gain blindly if it worsens Cin, CMRR, pseudoR behavior, or area.

## Power Decisions Must Separate Always-On And Duty-Cycled Blocks

For multi-channel MUX systems:

- Stage-1 is usually always-on; do not assume it can be power-cycled at the
  per-sample rate.
- Stage-2 may support standby/active modes if startup and settling pass.
- MUX/ADC driver blocks are usually better duty-cycling candidates.

Do not assume an unselected channel means the full AFE can be powered off. Any
duty-cycle proposal must pass wake-up, settling, baseline retention, noise, and
kickback simulations.

## Layout Decisions Must Start Early

Carry these layout assumptions before finalizing a schematic:

- Cin/Cf gain capacitors should use a unit MIM array when ratio accuracy
  matters.
- Use common-centroid, interdigitation, and dummy caps when mismatch matters.
- Route top and bottom plates symmetrically.
- Avoid placing critical input/feedback capacitors over noisy or asymmetric MOS.
- Decap and bias caps may overlap less sensitive MOS regions when appropriate.
- Post-layout extraction is mandatory for final CMRR, PSRR, and gain-error
  claims.

If Cf is below about 50 fF, explicitly check whether routing and fringe
parasitics dominate ratio error.

## Branch Decision-Record Template

At the end of each design branch, answer:

1. Which simulation checks are satisfied for the exact candidate revision: DC,
   AC, noise, STB, transient, CMRR, PSRR, MC, PEX?
2. Does it contain any functional ideal element: ideal resistor, ideal leak,
   behavioral source, 0 V tie, or fixed gate bias?
3. What is the worst corner, and why?
4. What is the current limiting mechanism: gm, headroom, pole ordering,
   pseudoR leakage, cap mismatch, supply feedthrough, noise contributor, or
   something else?
5. Is another sizing sweep likely to help? If two rounds gave small returns,
   stop sweeping and open a topology/root-cause branch.
6. Which metric improved and which got worse: power, Cin, noise, CMRR, PSRR,
   PM, area, recovery?
7. What is the technical object kind: proposal, analysis result, candidate
   nomination, diagnostic reference, rejected alternative, or historical
   informative reference?
8. What is the next smallest experiment that can distinguish at least two
   root causes?
9. If it is being nominated for a later gate, what remains open for device
   reliability, small-cap layout, high-Z nodes, PEX, startup/recovery,
   testability, trim/calibration, ESD/top-level interface, and DFM?

Record the answer with `governance/templates/decision-record.yaml`. The record
does not change gate state or create human authorization.
