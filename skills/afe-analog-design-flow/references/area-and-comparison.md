# Area And Literature Comparison

## Area Basis

Always state the area basis:

- MOS area proxy: usually `W*L*nf*multi`.
- MIM cap density assumption.
- rppoly resistor area mapping.
- pseudoR layout cell area.
- Whether MUX/ADC proxy caps are included.
- Whether output load proxy caps are included.
- Whether routing, guard rings, dummy devices, matching overhead, and final
  layout bounding boxes are excluded.
- Whether an accompanying floorplan image excludes simulation-only proxies.

For tapeout-oriented candidates, every per-channel addition must report area
per channel, power per channel, bias/reference wire count, trim bit count,
routing overhead, shared versus local implementation, and test observability.
Large capacitors, local well-bias drivers, trim DACs, and per-cell helper
circuits must be multiplied by the actual channel and cell counts.

## Avoid Mixed Bases

Do not mix:

- Early MFG compact snapshots.
- Clean INT area models.
- Layout-aware final estimates.
- PEX junction-area stress proxies.

If a topology changes, compute a delta table rather than silently replacing the
area number.

## Literature Table Rules

The "This work" row should include:

- Topology and node.
- Stage-1 `Cin` and `Cf`.
- Stage-2 gain caps and CMFB RC.
- pseudoR variant and well-bias topology.
- Clean area/ch and area/ch with backend proxy if used.
- Full-chain measured power, not stage-only power.
- Full-chain input-referred noise band.
- fHP/fLP and mismatch-aware CMRR/PSRR.
- Caveat that nominal/symmetric rejection is diagnostic only.

## Floorplan Handoff Rules

After updating the final area table, generate a physical-block floorplan
suggestion image using the same topology and area basis. Do not include MUX/ADC
or output-load proxies in the main physical-block floorplan unless they are
real layout blocks. If proxy context matters, make it a separate optional
comparison figure.

If explicit compensation capacitance exceeds 1 pF per channel, include an area
note. Treat per-channel capacitance above 5 pF as a layout red flag unless the
system area budget explicitly accepts it; capacitance above 20 pF requires
architecture review.

## Current INT090 Reference Values

Use these as a known example, not as universal constants:

- Clean AFE excluding MUX/ADC proxy and 50 fF output proxy: `0.010615 mm2/ch`.
- Clean AFE including 50 fF output proxy: `0.010715 mm2/ch`.
- With MUX/ADC proxy: `0.013517 mm2/ch`.
- Full-chain power: `5.455-6.049 uW/ch`.
- Full-chain gain at 1 kHz: `44.32-46.20 dB`.
- Full-chain noise 300 Hz to 10 kHz: `10.86-13.48 uVrms`.
- fHP: `2.76-58.35 Hz`.
- fLP: `24.8-28.75 kHz`.
- `CINP+0.1%` CMRR: minimum `80.01 dB` over 300 Hz to 10 kHz.
- `CINP+0.1%` VDD PSRR relative: minimum `83.32 dB` over 300 Hz to 10 kHz.
