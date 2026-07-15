# Legacy Project Migration

## Fail-Closed Compatibility Rule

Legacy checklists, handoffs, reports, plots, simulator directories, and prior
interface data are not imported as approvals or current promotion evidence.
Migration preserves engineering history without grandfathering lifecycle state.

## Migration Sequence

1. Freeze the legacy source tree and record its repository commit. Run
   `candidate_report_check.py` only as a file inventory.
2. Instantiate `governance/templates/project-state.yaml` for a new project ID.
   Keep every gate `not_started`, every approval reference null, and
   `template_only: true` until human owners, policies, baselines, and trusted
   signers are configured.
3. Import legacy decisions as `object_kind: proposal` or historical technical
   decision records. Import legacy results only in new manifests with
   `exploratory_only: true`, `promotion_eligible: false`, and their original
   project/candidate/provenance identity.
4. Compute the current source/spec/netlist/testbench/PDK/tool/policy hashes and
   set `template_only: false`. A migration actor may establish initial
   `not_started` records but cannot write `approved`.
5. Start at G0. Close G0-G10 sequentially through new independent reviews and
   verified human approvals. A legacy artifact may later be reissued as current
   promotion evidence only after semantic parsing, provenance rebasing,
   artifact digesting, applicable reruns, and independent review under the new
   scope.
6. Record every baseline-changing adaptation as an ECO/change record. Keep it
   blocking until its required revalidation exists and a verified human change
   authority closes or cancels it.

## Compatibility Outcomes

| Legacy item | New-model treatment |
|---|---|
| Checked Markdown box | Informative history; no state transition |
| “Passed/approved” prose | Informative history; no approval record |
| Existing simulation/report | Exploratory-only until reissued and validated |
| Other AFE/interface values | Proposal/reference only; never current validation |
| Old schematic candidate | New candidate ID and current evidence required |
| Old layout/PEX package | Exact layout/PEX hashes and current G8/G9 evidence required |
| Prior waiver | Recreate with current scope, owner, expiry, and human signature |
| Prior reviewer signoff | New schema-valid review bound to current scope digest |

There is no compatibility mode that disables predecessor approval, provenance,
freshness, metric semantics, independent review, or human authorization.
