# Layout Floorplan Suggestion

A floorplan is a G7 planning artifact, not layout, PEX, post-layout signoff, or
tapeout release. The INT090 pattern is `INFORMATIVE_ONLY` and cannot satisfy a
new project's mandatory artifact without current-project reproduction and
provenance.

Use this reference near the end of a candidate design, after full-chain
topology, block sizes, area basis, and major pass/fail metrics are known.

## Purpose

Generate an overall physical-block layout suggestion image, not a final layout
and not a pure area treemap. The image should help a human layout designer see
how the AFE should be organized before detailed device placement.

## Required Inputs

- Active topology and exact block list used in the electrical run.
- Stage-level `Cin`, `Cf`, gain caps, CMFB R/C, pseudoR cell counts, and
  well-bias driver counts.
- Area basis for every block.
- Which blocks are real physical AFE blocks and which are only simulation
  proxies, such as MUX/ADC load caps or output-load caps.
- Differential signal direction, common-mode loops, feedback loops, and special
  well/substrate connections.

## Drawing Rules

- Remove simulation-only proxy blocks from the physical-block floorplan. If a
  proxy is useful for comparison, show it in a separate optional figure.
- Place stages in signal-flow order from input to output.
- Preserve differential symmetry: draw P/plus and M/minus paths as mirrored
  regions when the circuit is differential.
- Put common-mode blocks such as CMFB RC islands on or around the symmetry axis,
  or otherwise label them clearly as common-mode rather than P/M signal blocks.
- Split capacitor and resistor arrays by function and side when that matches
  layout intent. Do not hide all caps inside one generic area box.
- Place pseudoR and pseudoR2 feedback banks near the feedback path they serve.
- Place well-bias drivers close to their pseudoR/PWELL/DNW nodes. Their drawn
  area may be small, but their routing and well taps are layout-sensitive.
- Leave visible routing corridors for input, interstage, output, bias, CMFB,
  DNW/PWELL/PSUB, and supply routes.
- Label the symmetry axis, stage boundaries, key capacitance/resistance values,
  pseudoR cell counts, and the area basis.
- Mark any precision capacitor below 50 fF as a layout-risk primitive unless
  the unit-cap array, parasitic estimate, mismatch handling, and PEX gain-error
  plan are already known.
- Show which bias/reference and well-bias circuits are local, shared, or
  global; for multi-channel systems, include the per-channel replication count.

## Output Artifacts

Produce at least:

- A PNG or SVG floorplan image.
- A block coordinate table with block name, x/y, width/height, area, category,
  and notes.
- A short report describing placement rationale, excluded proxies, and layout
  caveats.

## Sanity Checks

Before presenting the image:

- Verify it does not include MUX/ADC or output-load proxies unless explicitly
  labeled as non-physical optional context.
- Verify it is not just a packed rectangle treemap.
- Verify P/M symmetry is visible for differential blocks.
- Verify common-mode and feedback blocks are not drawn as unrelated lumps.
- Verify the drawn area matches the stated area basis within the expected
  rounding error.
- State that guard rings, dummy devices, matching arrays, final routing,
  well-spacing, and DRC overhead are still not captured unless the figure is
  explicitly layout-aware.
- State whether the figure assumes pre-fill or post-fill parasitics. High-Z
  nodes and small capacitor ratios need post-fill/PEX review before final CMRR,
  PSRR, and gain-error claims.
- Verify every fully differential left/right path has a visible matching
  strategy for caps, pseudoR, well-bias, active devices, CMFB, routing, and
  shielding.

## INT090 Example Pattern

For the INT090-style two-stage AFE:

- Keep stage-1 at the input side.
- Split stage-1 `Cin/Cf` into P and M halves near the input and stage-1 core.
- Put stage-1 pseudoR feedback banks along the top and bottom feedback regions.
- Use a narrow symmetric interstage LPF column between stage-1 and stage-2.
- Put stage-2 pseudoR2 banks at the top and bottom of stage-2.
- Split stage-2 gain caps and pseudoR2 well-bias drivers into P/M halves.
- Let the stage-2 active core span the symmetry axis.
- Put the stage-2 CMFB RC as a common-mode island rather than a differential
  signal block.
