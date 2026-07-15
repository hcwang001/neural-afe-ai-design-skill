---
name: afe-analog-design-flow
description: Governed analog front-end development lifecycle for Codex, covering AFE specifications, architecture comparison, PDK primitive characterization, behavioral modeling, DC-first transistor verification, mismatch-aware rejection, variation, layout readiness, PEX, post-layout signoff preparation, test/trim/calibration, ESD/interfaces, evidence provenance, and human-controlled phase gates.
---

# Governed AFE Analog Design Flow

Use this skill to perform AFE engineering inside a machine-readable lifecycle.
The technical workflow remains evidence driven, but a document, checklist,
simulation result, or Codex statement is never a gate authorization by itself.

## Non-Negotiable Authorization Boundary

Codex and all other automation may update a gate only to:

- `in_progress`
- `review_ready`
- `human_approval_required`
- `changes_required`
- `blocked`
- `stale`

Codex must never:

- write `approved`;
- create or imitate a human signature or signature-verification result;
- mark an independent review complete;
- approve a waiver;
- close or cancel an ECO/change record as a human authority;
- turn a Markdown checkbox, report statement, or filename hit into gate state;
- start gate `G(n+1)` before `G(n)` has an effective, verified human approval;
- use `exploratory_only` evidence for candidate promotion.

`not_started` is an initial/system state. `approved` is a human-only state and
is effective only when `scripts/gatekeeper.py` validates the exact approval
record, independent review, scope digest, current evidence, and all preceding
gates. The gatekeeper is read-only and may recommend
`human_approval_required`; it never grants approval.

## Machine-Readable Source Of Truth

Before continuing a project, locate and validate its instantiated project
state against:

- `governance/schemas/project-state.schema.json`
- `governance/policies/default-gates.yaml`
- `governance/policies/default-evidence.yaml`
- `governance/policies/default-authorization.yaml`

The project state, evidence manifests, requirements traceability, risk
register, technical decision records, ECO/change records, independent review,
waiver records, and human approval records are the lifecycle source of truth.
Handoffs and reports are derived views. Instantiated records are checked at
runtime against their JSON Schemas; schemas are not documentation-only.

If no instantiated project state exists, create only a draft from
`governance/templates/project-state.yaml`, leave it `template_only`, and request
the required human owners and baselines. Do not infer an approved state from
legacy handoffs.

Run, at minimum:

```text
python scripts/provenance_check.py --state <project-state.yaml>
python scripts/stale_evidence_check.py --state <project-state.yaml>
python scripts/gatekeeper.py --state <project-state.yaml> --gate <Gx>
```

## Governed Lifecycle

| Gate | Controlled output |
|---|---|
| G0 | Governance baseline |
| G1 | Requirements and electrode/ADC/PMU/top-level interface baseline |
| G2 | Architecture candidate |
| G3 | Qualified primitive/model baseline |
| G4 | Behavioral-model and verification baseline |
| G5 | Block schematic candidate |
| G6 | Integrated schematic candidate |
| G7 | Layout-ready candidate |
| G8 | PEX candidate |
| G9 | Post-layout signoff candidate |
| G10 | Tapeout release package |

The exact entry criteria, exit criteria, mandatory artifacts, and evidence
levels are defined in `governance/policies/default-gates.yaml` and
`references/workflow.md`. The policy, not this prose summary, is controlling.

Foundry MC is mandatory at G6 and G9 under the default policy. PEX is mandatory
at G8 and G9. Test/trim/calibration and ESD/top-level implementation closure are
mandatory at G7, with extracted/interface verification at G9. Before those
gates, related work may be exploratory but must not be promotion evidence.

## Engineering Sequence

1. Validate governance state and predecessor authorization.
2. Define controlling requirements and required evidence types before circuit work.
3. Compare multiple feasible architectures and retain rejected alternatives.
4. Characterize MOS, passive, leakage, pseudoR, well-bias, reliability, and
   layout-feasibility primitives before broad circuit sweeps.
5. Build full-chain budgets, loop/plant models, and measured-port updates.
6. Implement the smallest discriminating transistor block and run DC first.
7. Run AC/noise/rejection/stability only for DC-clean cases.
8. Replace functional ideal aids with verified PDK devices before transistor
   promotion evidence is created.
9. Integrate only reviewed block candidates; run deterministic PVT, mismatch,
   startup/recovery, and the gate-mandated variation evidence.
10. Close layout, PEX, test/trim/calibration, ESD, DFM, and external interfaces
    at their policy-defined gates.
11. Generate a derived handoff that reports machine state without changing it.

If the predecessor is not effectively human approved, the next gate must remain
`not_started`. Parallel activity is permitted only when every resulting
manifest has `exploratory_only: true` and `promotion_eligible: false`.

## Technical Invariants To Preserve

- Do not optimize a metric until the dominant mechanism is identified.
- Do not run blind W/L/current sweeps when a topology, leakage, matching,
  reference-path, or interface limitation dominates.
- Do not run full-chain sweeps to debug an unknown module.
- Do not trust a behavioral model that omits the suspected failure mechanism.
- Do not treat behavioral or functional ideal elements as transistor evidence.
- Do not treat equal ideal `R*C` products as physically equivalent. Preserve
  pole, zero, DC-blocking, damping, and distributed-parasitic roles when mapping
  compensation/filter networks to PDK devices.
- Use mismatch-aware CMRR/PSRR for design claims; nominal symmetry is only a
  diagnostic upper bound.
- Audit every pseudoR terminal and intent: `PSUB`, `DNW`, `PWELL`, `A`, `B`.
- Treat well-bias as leakage/low-frequency control unless system evidence
  requires wideband behavior.
- Audit every high-Z node for DC path, leakage, startup/reset recovery,
  parasitics, noise, rejection, shielding, and PEX sensitivity.
- Audit MOS terminal stress, voltage domains, startup/switching stress, bias
  realizability, matching, and manufacturability.
- Keep area basis consistent and tie the floorplan to the electrically verified
  topology. A floorplan is not an area treemap.
- Keep project-specific bands, corners, temperature, PM, mismatch, device, and
  MC thresholds in the approved project specification/overlay, not as universal
  skill constants.
- Do not publish PDK/model files, raw PEX, PSF/raw simulator databases, or
  private paper PDFs. Internal manifests may record identifiers and digests.

## Evidence And Freshness Rules

Keep object semantics explicit: a decision record with `object_kind: proposal`
is a proposal; an evidence manifest with `object_kind: analysis_result` is an
analysis result; a candidate is the gate-scoped `candidate_id`; and it becomes
an approved candidate only when a verified human approval is effective for the
current scope. None of these labels are interchangeable.

Each promotion manifest must bind the candidate to source/evidence commits,
spec/netlist/testbench hashes, PDK/model identity, simulator and command,
metric-extractor hash, timestamp, and artifact digest. MC and PEX/post-layout
levels add their policy-required fields.

The following changes invalidate dependent evidence until revalidated:

- source or included netlist;
- specification or requirements traceability;
- testbench, stimulus, measurement, or metric-extraction code;
- PDK release, model hash, model section, simulator, or command profile;
- layout, extraction deck, or PEX netlist;
- governing policy or schema baseline.

The `policy_hash` field is the canonical governance-contract hash over all
three loaded policies, the shipped JSON Schema bundle, and the read-only
governance engine scripts. Changing any of them causes a mismatch until the
baseline and dependent evidence are reissued.

Legacy or other-project evidence may be retained as `exploratory_only` or
`informative`, but project/candidate mismatches prohibit its use for promotion.

## Review, Findings, Waivers, And Decisions

- Use `references/project-gate-review.md` for project gates.
- Use `references/publication-review.md` only for publishing the skill.
- `BLOCKER` and `MAJOR` findings must not remain open when a gate is presented
  for human closure.
- BLOCKER is non-waivable under the default policy.
- A MAJOR waiver must have exact scope, human owner, expiry, compensating
  controls, revalidation triggers, and verified human authorization.
- Technical recommendations belong in decision records. They do not authorize
  promotion or close a gate.
- Every baseline-affecting ECO/change record is scope-bound. An applicable open
  change blocks promotion until revalidation is recorded and the change is
  closed or cancelled by a verified human change authority.

## Reference Routing

- `references/workflow.md`: controlling lifecycle semantics and gate sequence.
- `references/project-gate-review.md`: independent project review procedure.
- `references/publication-review.md`: public-skill publication review.
- `references/handoff-template.md`: derived, non-authoritative handoff.
- `references/migration-guide.md`: fail-closed import of legacy projects and
  evidence without grandfathered approvals.
- `references/simulation-gates.md`: DC-first simulation order and evidence
  meaning; simulation gates are not lifecycle authorization.
- `references/tapeout-ready-constraints.md`: reliability, layout, PEX,
  startup/recovery, test/trim/calibration, ESD, and DFM technical constraints.
- `references/decision-rules.md`: technical branch decisions and stop/switch
  rules; governance policy controls authorization.
- `references/specs-and-architecture.md`: requirements and architecture work.
- `references/device-sweeps-and-tables.md`: primitive characterization.
- `references/behavioral-modeling.md`: system and measured-port models.
- `references/block-playbook.md`: block-level technical guidance.
- `references/pseudo-resistor-well-bias.md`: pseudoR/well-bias implementation.
- `references/netlist-patterns.md`: sanitized netlists and connectivity review.
- `references/area-and-comparison.md`: area accounting.
- `references/layout-floorplan.md`: physical planning.
- `references/plots-and-reporting.md`: plot/report generation.
- `references/design-casebook.md`: informative historical lessons only; never
  current project state or promotion evidence.

## Scripts

- `scripts/gatekeeper.py`: authoritative read-only gate readiness evaluator.
- `scripts/provenance_check.py`: provenance and artifact-integrity checker.
- `scripts/stale_evidence_check.py`: baseline dependency/freshness checker.
- `scripts/candidate_report_check.py`: non-authoritative file inventory only.
- `scripts/pseudor_connectivity_audit.py`: first-pass pseudoR connectivity
  extractor; independent human review remains required.
- `scripts/extract_metrics.py`: reporting helper only unless its output is bound
  through an evidence manifest and current extractor hash.

No script in this skill is authorized to manufacture human approval.
