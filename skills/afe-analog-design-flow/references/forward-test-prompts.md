# Forward-Test Prompts

These prompts are qualitative usability checks only. They are not governance
acceptance tests and cannot replace `tests/test_gatekeeper.py` or machine policy
validation. A fresh thread must not be asked to infer gate approval from the
expected behavior text.

Use these prompts in fresh threads before publishing or after major revisions.
Pass only the skill path and raw task artifacts. Do not include expected
answers, hidden diagnoses, or prior conclusions.

## How To Run

1. Start a fresh thread or subagent.
2. Ask it to use this skill by name and path.
3. Provide one realistic task and the minimum required artifacts.
4. Review whether it loads project state/policies, runs the read-only gatekeeper,
   preserves predecessor authorization, avoids blind continuation, and produces
   proposals or analysis without writing human-controlled state.
5. Delete or isolate generated test artifacts before the next independent pass.

## Prompt 1: Continue From Handoff

```text
Use $afe-analog-design-flow at <skill-path> to continue this AFE project from
the provided handoff and instantiated project state. Derive the current gate
and usable evidence from state/policies/gatekeeper, then identify rejected
branches, open risks, and the smallest next experiment. Do not treat the
handoff as authorization.

Artifacts:
- <current handoff markdown>
- <latest report or metrics CSVs if available>
```

Expected behavior to check: the agent should not blindly continue the newest
branch; it should classify the phase and choose references such as
`workflow.md`, `decision-rules.md`, and `handoff-template.md`.

## Prompt 2: Audit A Passing Candidate

```text
Use $afe-analog-design-flow at <skill-path> to audit a schematic candidate whose
reported metrics appear to pass. Summarize which evidence is valid and current,
what is only schematic-level, and what remains before any promotion request.

Artifacts:
- <candidate report directory>
- <summary CSVs and plots>
- <netlist or connectivity audit if available>
```

Expected behavior to check: the agent should load
`tapeout-ready-constraints.md`, distinguish schematic PVT from signoff
evidence, and mention device reliability, small-cap layout, high-Z nodes,
startup/recovery, PEX, test/trim/calibration, and ESD/top-level risks.

## Prompt 3: Reopen A Rejected Topology

```text
Use $afe-analog-design-flow at <skill-path> to decide whether this previously
rejected topology should be reopened. Compare the old failure mechanism with
the new reason for reopening, and propose the smallest experiment that can
distinguish whether the old limitation still dominates.

Artifacts:
- <old rejected-branch report or case note>
- <new user request or new evidence>
```

Expected behavior to check: the agent should load `design-casebook.md` and
`decision-rules.md`, preserve the old rejection reason, and avoid repeating
blind sweeps.

## Prompt 4: Netlist Connectivity Rewrite

```text
Use $afe-analog-design-flow at <skill-path> to review this pseudoR/well-bias
netlist rewrite. Produce a connectivity audit table for every pseudoR-like
instance and identify terminal-order, DNW, PWELL, PSUB, sharing, and diagnostic
tie risks before recommending simulation.

Artifacts:
- <old netlist excerpt>
- <new netlist excerpt>
- <wrapper/subckt terminal order note if available>
```

Expected behavior to check: the agent should load `netlist-patterns.md` and
`pseudo-resistor-well-bias.md`, then ask for or infer terminal mapping instead
of assuming wrapper order is correct.

## Prompt 5: Final Report Packaging

```text
Use $afe-analog-design-flow at <skill-path> to package this candidate for a
human review. Generate a concise handoff outline, list missing evidence, and
say which plots, area tables, floorplan images, and project-gate artifacts are
missing. Keep reusable-skill publication review separate from project review.

Artifacts:
- <candidate run directory>
- <plots>
- <area table>
- <layout/floorplan suggestion>
```

Expected behavior to check: the agent should load `plots-and-reporting.md`,
`area-and-comparison.md`, `layout-floorplan.md`, and `handoff-template.md`, and
should not mix area bases or claim nominal rejection as final.
