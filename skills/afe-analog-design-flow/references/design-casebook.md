# Design Casebook

> **Governance classification: INFORMATIVE_ONLY.** This file contains historical
> project-specific observations and reusable reasoning patterns. It is not
> current project state, requirements, promotion evidence, independent review,
> or gate authorization. Candidate names, numeric values, and words such as
> passed/promote/freeze describe historical records only. A new project may use
> them solely as `exploratory_only` input until independently reproduced under
> its own project ID, baseline hashes, PDK, and evidence policy.

This casebook captures reusable decisions and failure modes from prior AFE
threads. It is intentionally not a chronological transcript. Use it when a new
task resembles an old decision, when a topology is being reopened, or when a
simulation result looks surprising.

## How To Use This Casebook

1. Match the current problem to a case below.
2. Reuse the reasoning pattern, not the exact numeric values.
3. Check whether the old evidence level was behavioral, standalone transistor,
   full-chain PVT, mismatch, MC, or layout.
4. If reopening a rejected path, state what new evidence makes it worth trying.

## Case A: Do Not Patch A Fragile High-R Output Node Forever

**Observed pattern**

- A high-output-resistance folded-cascode style LNA/CMFB route became sensitive
  to backend capacitance and common-mode actuation.
- CMFB patches accumulated: extra gm, RC, compensation, trims, and behavioral
  crutches.
- Stage-1 was being asked to solve too many jobs: low noise, high gain, backend
  drive, CMFB robustness, and ADC/MUX isolation.

**Decision**

- Pause the fragile high-R route as a reference.
- Move toward a two-stage AFE where stage-1 provides reasonable gain/noise and
  stage-2 handles remaining gain, bandwidth limiting, and backend isolation.

**Reusable lesson**

If a block needs repeated trim-like patches just to survive PVT or backend
loading, step back to architecture allocation. Do not keep making the same
node more elaborate until it becomes unlayoutable.

## Case B: Architecture B Was Not Rejected By Behavior Modeling Alone

**Observed pattern**

- Architecture B used a two-stage Miller-compensated stage-1 capacitive-feedback
  LNA with conventional transistor-level CMFB.
- Early closed-loop and STB diagnostics looked plausible.
- Real pseudoR feedback passed DC and pseudoR itself was not the main VoutCM
  failure mechanism.
- The limiting issue was extreme common-mode plant sensitivity: small control
  errors at the CMFB actuator produced tens of mV VoutCM error.

**Decision**

- Keep Architecture B only as a secondary cleanup/reference path.
- Do not reject it merely because a high-level chain model was incomplete.
- Do not promote it unless transistor-level CMFB centering can meet PVT targets
  without trim-like behavior or excessive power.

**Reusable lesson**

A behavior model can be useful and still miss the failure. When the failure is
CMFB centering, headroom, or plant gain, the model must include those paths.
Do not let either a passing or failing simplified model make the final call.

## Case C: Architecture C Won Because System Allocation Improved

**Observed pattern**

- Lower stage-1 gain plus a high-Z PGA/stage-2 path gave better backend loading
  isolation and allowed stage-2 to own neural-band bandwidth limiting.
- PGA input noise looked high by itself, but when referred through stage-1 gain
  and bandwidth allocation, total chain noise could meet the target.
- This shifted the design from "make stage-1 do everything" to "allocate
  gain/noise/LPF/backend drive across the chain."

**Decision**

- Prioritize Architecture C as the main path.
- Keep stage-1 gain moderate; stage-1 does not need to be 30 dB if the full
  chain reaches 40-60 dB.
- Stage-2 bandwidth should be neural-band appropriate; do not require 80-100
  kHz unless the system needs it.

**Reusable lesson**

Compare architecture-level noise and loading budgets before optimizing a single
block. A noisy-looking second stage may be acceptable after stage-1 gain, while
a heroic stage-1 may fail because it cannot drive the real backend.

## Case D: Standalone CMFB Can Under-Model The Integrated Plant

**Observed pattern**

- Standalone CMFB variants passed DC or phase margin in simplified testbenches.
- Some integrated versions failed because the actual common-mode plant,
  load/control-node poles, and actuator authority differed from the standalone
  assumptions.
- Repeated RC/cap sweeps improved local symptoms but did not solve the
  structural mismatch.

**Decision**

- Use standalone CMFB tests only for early feasibility.
- Move to measured-port/co-design behavioral models once integrated transistor
  data exists.
- Prefer defining required port behavior, loop UGF, actuator authority, and
  output/control impedance over continuing blind RC sweeps.

**Reusable lesson**

Loop design must include the plant it will drive. If standalone and integrated
results disagree, measure the integrated plant and update the model.

## Case E: Do Not Use Huge Capacitors As A Default Cure

**Observed pattern**

- Large MIM caps could stabilize some CMFB/servo behaviors.
- The required caps often reached thousands to tens of thousands of square
  microns, dominating channel area.
- Smaller physical RC options sometimes worked as diagnostics but raised
  resistor spread, noise, parasitic, and layout concerns.

**Decision**

- Treat large caps as benchmarks or emergency fallbacks, not first choices.
- Use device/primitive tables and behavior models to find lower-area structural
  solutions.

**Reusable lesson**

If the only passing solution is a huge capacitor, ask whether the topology,
port impedance, or loop allocation is wrong.

## Case F: PseudoR Return Was Not A Free Fix

**Observed pattern**

- Adding an independent pseudoR return to the summing node worsened noise in
  the old Architecture-B pseudoR trial.
- Real pseudoR feedback alone could provide enough DC path in that context.
- A diagnostic exact 100 GOhm return was misleading because its own noise could
  dominate.

**Decision**

- Do not target an exact 100 GOhm ideal resistor.
- Use extracted pseudoR models and test whether feedback already provides the
  required DC path.

**Reusable lesson**

A DC return that looks harmless in ideal form can become a noise or leakage
problem when implemented physically. Always include thermal/leakage/noise and
PEX diode behavior.

## Case G: Well-Bias Is Slow Leakage Compensation, Not Automatically A Buffer

**Observed pattern**

- pseudoR well-bias driver design initially drifted toward generic buffer/OTA
  attempts.
- Behavioral requirement modeling clarified that DNW often needs slow tracking
  of PWELL with adequate low-frequency output impedance and PSRR, not wideband
  following.
- Very low current can simulate well but may be manufacturing-risky if current
  mirrors and mismatch are unrealistic.

**Decision**

- First model required DC tracking, bandwidth, Rout, PSRR, and load.
- Then implement a low-power but manufacturable MOS driver, usually with
  explicit current mirror bias rather than fragile self-bias.

**Reusable lesson**

Before designing an auxiliary loop, write the requirement in system terms.
Avoid optimizing a circuit metric that the system does not need.

## Case H: pseudoR2 Improved fHP But Did Not Magically Save Area

**Observed pattern**

- Stage-2 pseudoR2 with two series cells per side improved high-pass behavior
  and full-chain robustness.
- It reduced the number of stage-2 pseudoR cells, but independent 16x well-bias
  drivers added MOS area.
- Net channel area improved only modestly under the clean INT area model.

**Decision**

- Promote pseudoR2 based on electrical behavior and robustness, not an assumed
  large area win.
- Update area with the exact topology rather than reusing old pseudoR cell
  counts.

**Reusable lesson**

When a cell count decreases, check the supporting bias/driver area. Area wins
often move rather than disappear.

## Case I: Current Reduction Can Improve A Metric For The Wrong Reason

**Observed pattern**

- Lower current sometimes improved apparent full-chain behavior.
- The improvement could come from changed operating point, pole placement,
  loading, or headroom, not because less current is universally better.
- Very low current may create mismatch/startup/manufacturability risk.

**Decision**

- Analyze operating point, gm/gds, pole/zero movement, noise contributors, and
  headroom before promoting low-current points.
- Keep practical current mirror replication and device sizing in view.

**Reusable lesson**

Treat lower current as a design variable, not a moral victory. Robustness,
matching, startup, and bias replication matter.

## Case J: CMRR/PSRR Must Be Mismatch-Aware

**Observed pattern**

- Nominal/symmetric CMRR and PSRR often produced very high numbers or numerical
  artifacts.
- Deterministic capacitor mismatch gave smooth, believable passband rejection
  curves.
- A 10x smaller capacitance mismatch produced roughly 20 dB better rejection,
  matching expectation.

**Decision**

- Use nominal CMRR/PSRR only as smoke tests.
- Use deterministic mismatch curves, such as `CINP+0.1%`, for final plots and
  comparison claims.

**Reusable lesson**

If a rejection number depends on perfect symmetry, it is not a design claim.

## Case K: Area Basis Drift Can Corrupt Comparisons

**Observed pattern**

- Early MFG area snapshots and later clean INT area models counted pseudoR
  cells and well-bias drivers differently.
- Reusing old area numbers after topology changes created misleading
  comparisons.

**Decision**

- State the area basis every time.
- Use delta tables when switching pseudoR cells, drivers, caps, or backend
  proxies.

**Reusable lesson**

Area is a model until layout. Never mix area bases in a literature row.

## Case L: Handoffs Are Design Artifacts

**Observed pattern**

- Long chats lose context; wrong old architecture can be revived accidentally.
- A dated handoff with current mainline, rejected branches, metrics, reports,
  and next step prevents backtracking.

**Decision**

- Keep old handoffs as historical evidence, but mark superseded files clearly.
- Prefer a dated current handoff for the active design state.

**Reusable lesson**

For long analog projects, the handoff is part of the design database.

## Case M: Floorplan Suggestion Is Not An Area Treemap

**Observed pattern**

- A first layout sketch can accidentally become a packed area diagram.
- Including MUX/ADC or output-load proxy blocks in the main physical layout
  picture makes the AFE look larger or differently organized than the real
  circuit.
- Differential symmetry, common-mode blocks, feedback paths, and well-bias
  locality are easy to lose if the image is generated directly from an area
  table.

**Decision**

- Generate a final physical-block floorplan suggestion after area accounting.
- Exclude simulation-only proxies from the main floorplan.
- Draw P/M symmetry, stage boundaries, common-mode islands, feedback banks,
  and local well-bias placement explicitly.
- Keep a coordinate/area table next to the image so the drawing remains
  auditable.

**Reusable lesson**

The floorplan image should communicate layout intent, not merely conserve area.

## Case N: Stage-2 CMFB Compensation Must Be Mapped By Mechanism

**Observed pattern**

- The exact INT089/INT090-derived stage-2 still depended on an ideal
  `10Mohm/250fF` CMFB branch whose final integrated stability had not been
  closed.
- Removing compensation gave about `41.8deg` worst-case phase margin. A pure
  capacitor made phase margin worse, while a pure resistor broke DC because the
  capacitor was also isolating two CMFB bias nodes.
- Equal nominal `R*C` products behaved differently because the series resistor
  supplied phase lead; the design requirement was not one time constant.
- Co-designing the CMFB source mirror, fixed load, correction actuator, and RC
  branch produced a narrow ideal boundary. `5Mohm/550fF` only barely crossed
  `60deg`, while `6Mohm/450fF` retained useful margin.
- Three no-RC routes were tested separately: fixed-load recentering,
  source-current/load co-design, and a weaker actuator mirror. Each could find
  six-corner DC points, but their worst phase margins stayed structurally low,
  roughly `26deg..46deg`.
- Mapping the finalist to a distributed PDK `rppolywo_m` resistor and a
  `24um x 24um` `mimcap_sin` changed the model materially. The resistor alone
  contributed about `392fF..433fF` body capacitance, comparable to the explicit
  MIM value of about `549fF..673fF`.

**Decision**

- Close the no-RC branch for the current single-stage CMFB topology. Reopen it
  only after an architecture change, not another local sizing sweep.
- Freeze INT101 with the physical distributed-R plus MIM-C branch after exact
  module PVT/STB, AC/noise, and common-mode pulse recovery.
- Keep the physical topology in the clean exported core; do not replace it with
  an ideal `6Mohm/450fF` shorthand.
- Treat module promotion and full-chain promotion as separate gates. After
  Stage-2 closure, full-chain work can remain paused while Stage-1 is reopened.

**Evidence and outcome**

- Physical stage-2 passed CMFB `diffstbprobe` in `6/6` process-temperature
  corners with `62.85deg` minimum phase margin.
- A `5nA/side`, `100us` output common-mode disturbance recovered to `+/-1mV` in
  `7us..10us` across all six corners.
- The physical RC estimate was about `1660.47um2`, about `19.3%` below the old
  ideal `10Mohm/250fF` proxy, despite including the parasitic structure that
  actually stabilizes the loop.

**Reusable lesson**

Optimize compensation in this order: identify each component's role, establish
the ideal requirement boundary, co-design only mechanism-linked devices, close
structurally failing alternatives, map to distributed PDK passives, rerun exact
module gates, and only then freeze a clean netlist. Area and stability claims
made before physical-passive mapping are provisional.

## Case O: Stage-1 Auxiliary Noise, Gain Recovery, And Artifact Reset

**Observed pattern**

- Separate-noise analysis showed that eight local pseudoR well-bias drivers
  contributed noise comparable to the input pair and output load. The
  input-adjacent cell dominated the driver contribution.
- Replacing four pseudoR1 cells per side with one pseudoR2 cell reduced
  low-frequency density, power, and fHP spread, but PEX feedback capacitance
  reduced gain and initially worsened integrated input-referred noise.
- Reducing an already risky 10 fF feedback capacitor was not acceptable. A
  moderate Cin increase recovered gain while retaining input-impedance margin.
- A fixed 3 ms overload-recovery deadline conflicted with the intentional
  low-Hz high-pass pole. Natural recovery was slow, while reasserting the real
  reset MOS after the artifact gave robust recovery.
- The validated generator still hid ideal bias currents inside the block until
  they were moved to explicit ports and regression tested.
- A final bounded current/input-area/well-bias-area scan improved noise but did
  not close the hard target before power and output-common-mode penalties
  appeared.

**Decision**

- Include local well-bias/servo circuits in contribution analysis and scale
  the most strongly coupled positions first.
- Evaluate pseudoR changes with gain, integrated noise, fHP, input impedance,
  area, and rejection together.
- Recover a parasitic-driven gain loss on the physically safer capacitor; do
  not shrink a parasitic-dominated Cf merely to improve the nominal ratio.
- Separate natural high-pass recovery characterization from reset-assisted
  artifact recovery. Make reset/blanking a system interface when required.
- Freeze a clean core only after ideal sources are exposed as ports and the
  cleaned hierarchy numerically matches the promoted candidate.
- Close local sizing when several co-dominant contributors remain and the best
  bounded move still misses the target. Open a topology/noise-efficiency or
  specification branch instead.

**Reusable lesson**

Auxiliary circuits and interfaces can dominate an AFE decision even when the
main amplifier schematic is unchanged. Optimize the whole local feedback
ecosystem, then regression-test the exported core.
