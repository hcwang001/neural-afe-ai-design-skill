# AFE Decision Rules

Use this reference whenever a design branch is being planned, evaluated,
promoted, paused, or rejected. The goal is to prevent blind simulation and to
turn each branch into evidence.

## Core Rule

Do not optimize a metric until the dominant mechanism is identified. Do not
promote a candidate unless it passes the appropriate gate without functional
ideal aids. Do not keep sweeping device sizes when the failure pattern indicates
a topology, leakage, matching, or reference-path limitation.

For tapeout-oriented work, do not promote a candidate solely because schematic
PVT passes. A promoted candidate must be physically realizable,
reliability-clean, mismatch-aware, startup-safe, layout-aware, and backed by a
PEX/test/trim plan when those risks apply. Read
`tapeout-ready-constraints.md` before calling a candidate final.

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

Run transistor gates in this order unless doing an explicitly labeled
diagnostic shortcut:

1. DC operating point.
2. AC, gain, and bandwidth.
3. Noise.
4. Stability, preferably with `diffstbprobe` or an equivalent differential
   loop method.
5. Transient startup and recovery.
6. CMRR and PSRR with deterministic mismatch.
7. PVT plus Monte-Carlo.
8. Post-layout extraction.

No AC, noise, or STB claim is valid unless the same candidate has already
passed a clean DC gate without functional ideal elements.

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
  for early exploration, but not final signoff.
- Functional 250 Mohm, 1 Tohm, or similar huge ideal resistors are red flags.
- Behavioral CMFB or VCVS blocks are architecture exploration only, not a
  transistor-level candidate.
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
- PM >= 60 degrees across required corners, with modest compensation cap when
  possible.

Avoid:

- One high-Z gate node controlling the entire main load.
- Per-side fast servos that respond to differential signal.
- Huge compensation cap as the primary solution.
- Wideband followers where a slow servo is required.

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

Typical first targets:

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

## CMRR And PSRR Must Be Mismatch-Aware

Nominal symmetric CMRR/PSRR is an upper bound only. Design decisions must use
deterministic mismatch first and later PDK Monte-Carlo.

Useful deterministic stresses:

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

A reasonable default target is around 40 dB total gain with roughly 30-50 dB
programmable range. Do not increase stage-1 gain blindly if it worsens Cin,
CMRR, pseudoR behavior, or area.

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

## Branch Closure Template

At the end of each design branch, answer:

1. Which gates did this candidate pass: DC, AC, noise, STB, transient, CMRR,
   PSRR, MC, PEX?
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
7. What is the candidate's status: final candidate, baseline, diagnostic
   reference, rejected, or historical passing reference?
8. What is the next smallest experiment that can distinguish at least two
   root causes?
9. If it is being promoted toward tapeout, what remains open for device
   reliability, small-cap layout, high-Z nodes, PEX, startup/recovery,
   testability, trim/calibration, ESD/top-level interface, and DFM?
