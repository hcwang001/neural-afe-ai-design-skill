# Netlist Patterns

Netlists used as promotion evidence must be content-addressed and bound through
an evidence manifest to the candidate ID, source/evidence commits, complete
include digest, testbench, PDK/model, and policy baseline. A sanitized/public
netlist is not automatically identical to the internally simulated netlist.

## Clean Netlists

- Generate a sanitized public candidate netlist for each nominated run when
  disclosure is allowed, while retaining the internal content digest.
- Keep generated wrappers next to the run report.
- Avoid long include chains when a clean inline wrapper is safer.
- Name variants with stable run IDs such as `INT090`, `MFG066`, or `WBDRV001`.

## Dependency Control

- When a netlist starts depending on too many older files, create a cleaned
  export that contains only the active subckts and wrappers.
- Preserve user or prior-agent edits; do not revert unrelated files.
- Keep diagnostic netlists separate from candidate netlists.

## Connectivity Audits

For any structural rewrite, emit an audit table:

- Instance name.
- Subckt name.
- Node mapping.
- Old cell count and new cell count.
- Deleted legacy devices.
- Added devices.

For pseudoR devices, always audit:

- `PSUB`: usually substrate/ground.
- `DNW`: usually driven by well-bias driver output or tied to a safe rail for
  diagnostic tests.
- `PWELL`: usually connected to the local pseudoR internal/common node that the
  driver senses.
- `A` and `B`: signal terminals; verify series orientation when the PEX pin
  order differs from the wrapper order.

Use `scripts/pseudor_connectivity_audit.py` as a first-pass extractor for
sanitized Spectre/SPICE-style netlists. The script does not prove correctness;
it creates a table that makes manual PSUB/DNW/PWELL/A/B review harder to skip.

## Naming Conventions

- Use `stage1`, `stage2`, `fullchain`, `pseudor`, `wellbias`, and `mismatch`
  explicitly in file names.
- Include the run ID in generated CSV and plot names.
- Keep report titles human-readable and include the active topology.

## GitHub Safety

Do not publish:

- PDK models, foundry decks, private model sections.
- Raw PEX netlists unless cleared.
- PSF/raw Spectre databases.
- Private papers or copyrighted PDFs.
- Absolute machine-specific paths as required paths.

Prefer publishing:

- Workflow docs.
- Parameterized scripts.
- Sanitized report templates.
- Extracted metrics and plots when allowed.
