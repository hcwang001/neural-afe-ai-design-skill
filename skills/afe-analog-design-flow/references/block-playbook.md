# Block Playbook

Use this reference for block-level design judgment. It complements the phase
flow and casebook with practical rules for common AFE blocks.

This playbook is technical guidance only. Numeric gains, voltages, loads,
capacitances, bandwidths, and device examples are historical starting points;
the approved project requirements/PDK overlay controls. "Promoted" means
candidate nomination for machine/human review, never gate approval.

## Stage-1 LNA

### What Stage-1 Should Own

- Input-referred noise.
- Input impedance.
- Moderate front-end gain.
- Electrode/common-mode compatibility.
- Stable capacitive feedback and high-pass behavior.

### What Stage-1 Should Not Necessarily Own

- All 40-60 dB of full-chain gain.
- Final neural-band low-pass filtering.
- Heavy MUX/ADC/backend drive.
- Complex trim-like common-mode rescue.

### Design Lessons

- Do not force 30 dB stage-1 gain if 20-25 dB plus a good stage-2 meets the
  total chain target.
- Increasing `Cin/Cf` gain can reduce input-referred downstream noise, but
  increases input cap area and may affect input impedance and mismatch-driven
  CMRR.
- Increasing gain reduces ADC quantization impact, but does not improve analog
  input-referred SNR once ADC noise is already below analog noise.
- Power reduction should be judged by noise, operating point, headroom, and
  manufacturability, not just nominal PVT pass.
- Common-mode changes such as 0.5 V input/output bias must be checked at the
  stage interface, not only locally.
- Stage-1 `Cin/Cf` values below about 50 fF on the feedback side are
  layout-risk primitives; require unit-cap, parasitic, mismatch, and PEX
  gain-error review before final claims.
- Include pseudoR well-bias drivers, local servos, and bias mirrors in the
  Stage-1 noise-contribution table. Position-aware sizing can outperform
  uniform scaling when one feedback cell is closest to the summing node.
- A pseudoR replacement can lower low-frequency noise yet worsen integrated
  input-referred noise by reducing signal gain through PEX capacitance. Review
  gain and noise together.
- If gain must be recovered, prefer increasing Cin only while input impedance,
  area, and mismatch remain acceptable; do not shrink an already
  parasitic-dominated Cf by default.
- Characterize natural artifact recovery on the fHP time scale. When fast
  recovery relies on real reset MOS, verify the reset-assisted sequence and
  carry reset/blanking into the top-level interface requirements.
- A promoted Stage-1 core should expose external bias nodes explicitly and
  keep ideal reference currents in a separate regression harness.

## Stage-2 PGA/VGA

### What Stage-2 Should Own

- Remaining gain.
- Neural-band low-pass filtering.
- Backend load isolation.
- Output common-mode and ADC/MUX interface.

### Design Lessons

- A high standalone input-referred PGA noise may be acceptable after stage-1
  gain referral.
- The output pole should not accidentally define the final neural LPF unless it
  is controlled across PVT and load.
- Stage-2 pseudoR and CMFB choices can dominate high-pass behavior and output
  offset.
- Backend load should be explicit: preferred load assumptions such as 50 fF/side
  should be simulated and recorded.
- Treat physical CMFB compensation as part of the stage, not as a schematic
  annotation. Its resistor body capacitance, spread, noise, and area can change
  both the loop and the apparent area optimum.

## CMFB

### Design Questions

- What node does CMFB sense?
- What actuator does it control?
- What is the plant gain from actuator to output common-mode?
- What are the output and control-node poles?
- What UGF range is needed by the integrated system?
- What cap/resistor area is acceptable?

### Design Lessons

- Use `diffstbprobe` or an equivalent differential loop method; do not call a
  single-ended `iprobe` result differential stability.
- Standalone CMFB is an early screen; integrated plant modeling is required.
- Characterize actuator-to-VoutCM gain/phase, output CM impedance, control-node
  impedance, CMFB sensing pole, actuator gm, and differential contamination.
- If repeated cap sweeps are needed, ask whether output/control impedance or
  actuator authority is wrong.
- Prefer true common-mode sensing, a low-Z/buffered control node, fixed main
  load plus a small correction branch, and modest correction gm.
- Avoid one high-Z gate controlling all main load, per-side fast servos that
  respond to differential signal, and huge compensation caps as the primary
  fix.
- Prefer measured-port/co-design models when transistor data exists.
- A series CMFB resistor may create the required phase-lead zero; preserving
  only the nominal `R*C` product can destroy stability or DC behavior.
- For multi-megaohm PDK resistors, include distributed body/routing capacitance
  when it is comparable to the explicit compensation capacitor.
- Do not call a CMFB loop tapeout-ready from a single-ended `iprobe` result;
  use a proper differential/CMFB loop method and include startup/reset
  recovery.

## PseudoR Feedback And Input Returns

### Design Questions

- Is an extra input/summing-node return actually needed?
- Does the pseudoR feedback itself provide a DC path?
- What is the noise contribution of the return element?
- What fHP range results from extracted leakage across PVT?
- Are DNW diode model sections included?

### Design Lessons

- Do not design around an exact 100 GOhm ideal resistor.
- Extra pseudoR returns can worsen noise.
- PEX pseudoR models must include required diode sections.
- A pseudoR topology that passes DC can still fail noise, fHP, or mismatch.
- pseudoR series count is not validated unless fHP scales as expected. If
  series count barely changes fHP, inspect endpoint/well/DNW/PSUB leakage.

## Well-Bias Driver

### Design Questions

- Is DNW supposed to track PWELL slowly, or follow it wideband?
- What tracking error is acceptable?
- What bandwidth is required?
- What output impedance is required in-band and at low frequency?
- What current is manufacturable and mirrorable?

### Design Lessons

- Model the required driver before transistor implementation.
- Treat DNW/PWELL control as a slow leakage-compensation servo unless proven
  otherwise; do not default to a wideband unity follower.
- Avoid fragile self-bias unless it has clear startup and PVT evidence.
- Bias through explicit current mirrors when practical.
- Very low current may be acceptable only if mismatch, startup, leakage, and
  mirror sizing are credible.
- Independent per-cell drivers can improve locality but increase MOS area.
- Before promotion, report whether the driver bias is realizable, mirrorable,
  reliable across voltage domains, and replicated locally or shared across
  cells/channels.

## Interstage LPF And Backend Interface

### Design Questions

- Should LPF be set by controlled R/C, parasitic output poles, or stage-2 loop
  behavior?
- What is the resistor noise contribution referred to the input?
- What area and parasitic capacitance does the physical R/C imply?
- What backend load is being isolated?

### Design Lessons

- Do not assume a very large resistor is cheap; rppoly length, body capacitance,
  noise, and spread matter.
- Do not let uncontrolled output loading set the signal bandwidth.
- Treat MUX/ADC proxy caps separately from core AFE area unless they are truly
  part of the per-channel analog core.
- Keep final neural bandwidth, stage differential bandwidth, CMFB crossover,
  pseudoR/HPF cutoff, and interstage/ADC settling bandwidth separate.
- Any large RC compensation or filtering element needs area, spread, parasitic,
  and PEX sensitivity notes before it becomes a final schematic choice.

## Noise, Gain, And Power Decisions

- Decompose noise before increasing current. If current does not reduce the
  dominant noise contributor, stop increasing it.
- Report input pair, output load, pseudoR, CMFB, bias/reference, stage-2, and
  total-chain input-referred noise when possible.
- Choose gain from input range, artifact swing, ADC full-scale/LSB, analog
  input-referred noise, stage output swing, and gain-code coverage.
- Separate always-on and duty-cycled blocks. Do not assume an unselected
  channel means the full AFE can be powered off.

## Plot And Report Interpretation

- Gain should show intended high-pass and low-pass behavior.
- Noise should be referred through the correct gain path.
- CMRR/PSRR should be smooth in the passband when using deterministic mismatch.
- Low-frequency notches during high-pass transition should be documented rather
  than mistaken for passband behavior.
