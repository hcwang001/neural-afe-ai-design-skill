# Device Sweeps And Tables

## Purpose

Use primitive characterization to avoid blind circuit sweeps. The output should
be tables that bound feasible W/L, current, gm/Id, capacitance, resistance,
noise, leakage, and area.

## MOS Tables

Build tables across relevant PVT corners for:

- gm/Id.
- gm/gds.
- Id, gm, gds.
- VDS margin and region.
- Gate, diffusion, and well capacitances.
- Thermal and flicker noise indicators.
- Mismatch sensitivity when available.
- Area proxy `W*L*nf*multi`.

Use the table to choose realistic current densities and device sizes. Do not
select ultra-small currents solely because a nominal simulation passes.

For analog-critical paths, do not use minimum-length or minimum-width MOS
devices unless speed, capacitance, or switch on-resistance explicitly requires
it. Report why the size is safe for mismatch, flicker noise, ro, PVT drift,
layout edge effects, and DFM.

For current mirrors, bias references, replica devices, and CMFB bias branches,
prefer longer-than-minimum `L`, report VDS matching and saturation margin, and
avoid extreme weak inversion unless mismatch and leakage have been verified.

Every final device-size choice should state the tradeoff among noise, gain,
headroom, capacitance, mismatch, layout area, and stability. If the winning
point relies on extreme W/L, ultra-low current, or leakage-dominated behavior,
mark it high-risk and read `tapeout-ready-constraints.md`.

## Passive Tables

For each passive option, tabulate:

- Nominal value.
- PVT spread.
- Thermal noise contribution.
- Parasitic capacitance.
- Area.
- Voltage coefficient or stress limits.
- Layout feasibility.

Typical options:

- MIM capacitors.
- MOSCAP using 1.8V devices when safe.
- rppoly or other available resistors.
- MOS triode/off/regulated pseudo-resistors.
- Extracted pseudoR cells.

## PseudoR Tables

PseudoR tables should include:

- Cell version and PEX/source file.
- Terminal order.
- Area and bounding-box estimate.
- Leakage versus PVT and bias.
- Effective high-pass impact in the intended circuit.
- PWELL/DNW/PSUB biasing requirement.
- Whether well-bias is local, shared, or absent.

Any leakage-dominated primitive, including pseudoR, MOS-off return,
subthreshold active-R, ultra-weak bleed, or well-bias leakage compensation,
requires temperature, FF/SS leakage, well/DNW/PSUB leakage, mismatch, startup,
long-transient, noise, and PEX-sensitivity evidence before promotion.

## Sweep Discipline

- Sweep one physical question at a time.
- Keep a short table of candidates rather than a giant unreviewable run.
- Stop sweeping when the failure is structural.
- Convert repeated sweep failures into a behavioral requirement or new
  architecture question.
