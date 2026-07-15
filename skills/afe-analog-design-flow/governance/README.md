# AFE Governance Data Model

This directory contains the machine-readable lifecycle contracts used by the
read-only gatekeeper.

## Authority

- `policies/default-gates.yaml` defines G0-G10, predecessors, stages, and
  mandatory artifacts.
- `policies/default-evidence.yaml` defines evidence levels, provenance,
  freshness, metric parsing, and proxy restrictions.
- `policies/default-authorization.yaml` defines automation states and human
  review/approval roles.
- JSON Schemas define project state, evidence, review, waiver, approval,
  technical decision, ECO/change-control, and trusted signer records. The
  gatekeeper applies Draft 2020-12 validation at runtime and fails closed when
  the validator dependency is unavailable.

Markdown reports and handoffs are derived views. They are never authoritative
state.

`current_baseline.policy_hash` is computed over the three loaded policies, the
complete JSON Schema bundle, and the four enforcement scripts, so a schema-only
or gatekeeper-code change also invalidates the old governance contract.

## Human Signatures

Completed review, approval, waiver, and ECO/change-closure records use Ed25519
signatures. The project's `trusted-signers.yaml` contains public keys and
allowed roles only; private keys must remain outside Codex and outside the
skill repository.

The canonical signed payload is implemented by
`scripts/governance_common.py::signature_payload`. It binds the record type,
project/gate/candidate identifiers, current scope digest, review digest,
decision/findings, human identity/role, and signing timestamp. The scope digest
also binds requirements, risks, decisions, ECOs, waivers, policies, trusted
signer registry, baseline, and promotion evidence. Gatekeeper verifies the
signature against the enabled project signer registry and rejects
actor/key/role mismatches or any changed signed field.

The organization remains responsible for human identity proofing, private-key
custody, key revocation, protected-branch/CODEOWNERS enforcement, and release
approval quorum. Codex must not possess a human private key or invoke a human
signing action.

## Templates

Templates intentionally contain placeholders, no completed review, no active
waiver approval, and no approved gate. Instantiate them in a project-controlled
location, compute current hashes, set `template_only: false`, and run the three
governance checks before requesting independent review.
