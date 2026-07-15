# Skill Publication Review

## Scope

This review applies only to publishing or installing the reusable skill. It
must not be cited as project design evidence or as a lifecycle approval.

## Required Publication Conditions

The publisher should verify that:

- SKILL.md routes users to the machine-readable governance policies and does
  not authorize Codex to write human states.
- schemas, default policies, templates, gatekeeper, provenance/stale checkers,
  and automated tests are included and mutually consistent;
- public examples are clearly informative and cannot be selected as current
  project evidence;
- project-specific bands, corners, temperature, PM, mismatch, MC, device, and
  area values are identified as examples or overlays rather than universal
  gate requirements;
- PDK/model files, raw PEX, PSF/raw simulator databases, private model sections,
  private handoffs, and copyrighted PDFs are absent;
- no local absolute path is required for normal use;
- no template contains an approved gate, completed independent review, active
  waiver approval, verified signature, or tapeout-release assertion;
- all governance and technical tests complete successfully.

## Publication Record

Publication disposition belongs in the repository release/CI record. It does
not belong in an AFE project state and does not close G0-G10.
