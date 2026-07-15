# Independent Project Gate Review

## Authority Boundary

This procedure prepares and records an independent human technical review. It
does not itself approve a gate. Gate approval is a separate human action bound
to the same scope digest.

Codex may assemble a draft review package and findings, but must leave reviewer
identity/signature fields incomplete and must not change review status to
`completed`.

## Review Inputs

The reviewer receives:

- instantiated project state and controlling policy versions;
- exact candidate ID and gatekeeper-generated scope digest;
- requirements traceability and applicable controlling metrics;
- all mandatory evidence manifests and provenance/stale reports;
- risk register, decision records, ECOs, and proposed/active waivers;
- gate-specific technical artifacts from `default-gates.yaml`.

The reviewer must not accept handoff text, filenames, plots, or raw simulator
directories in place of evidence manifests and parsed metrics.

## Independence

The completed record must identify a real human reviewer with an externally
verifiable signature reference. The reviewer must not be one of the candidate
authors and must hold a role allowed by `default-authorization.yaml`.

## Finding Classification

- `BLOCKER`: invalid identity/provenance, stale mandatory evidence, controlling
  requirement failure, unsafe/reliability violation, missing mandatory artifact,
  authorization conflict, or equivalent release-preventing issue. It is not
  waivable under the default policy.
- `MAJOR`: material risk to function, yield, manufacturability, testability,
  interface closure, or conclusion credibility. It must be closed or covered by
  a valid scoped waiver.
- `MINOR`: non-material issue that still requires disposition, owner, and due
  gate/date.

An open BLOCKER or MAJOR prevents gate readiness. A finding marked `waived`
must reference a waiver that the gatekeeper independently validates.

## Technical Review Focus

Review the gate-specific mandatory artifacts and, where applicable:

- DC-first execution and operating-region/headroom evidence;
- architecture and behavioral-model consistency;
- functional ideal/proxy exclusion from transistor claims;
- mismatch-aware CMRR/PSRR and MC configuration;
- high-Z, pseudoR/well-bias, startup/recovery, and reliability;
- layout feasibility, matching/symmetry, area basis, and parasitic sensitivity;
- PEX/post-layout identity and extracted re-verification;
- test/trim/calibration, ESD, electrode, ADC, PMU, and top-level interfaces;
- provenance, freshness, metric-extractor version, and change-control impact.

## Completion Record

Use `governance/templates/gate-review.yaml` and validate it against
`governance/schemas/gate-review.schema.json`. Completion requires:

- exact project/gate/candidate IDs;
- current scope digest from gatekeeper;
- candidate author list;
- completed findings and waiver references;
- independent human identity, role, time, and verified external signature
  reference.

After completion, rerun gatekeeper. A clean review may permit the tool to report
`human_approval_required`; it is not an approval.
