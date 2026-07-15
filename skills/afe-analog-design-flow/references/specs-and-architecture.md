# Specs And Architecture

## Specification Table

Create a table like this before architecture work:

| metric | preferred | acceptable | evidence required | notes |
|---|---:|---:|---|---|
| Signal band | | | | |
| Total gain | | | | |
| Stage gain split | | | | |
| Input-referred noise | | | | |
| Power/channel | | | | |
| Area/channel | | | | |
| fHP / fLP | | | | |
| Input impedance | | | | |
| Backend load tolerance | | | | |
| CMRR / PSRR | | | | Include mismatch condition. |
| Startup / recovery | | | | |
| MC yield | | | | |

If a value is missing, Codex may propose a provisional value from system
context, but it must remain a `proposal` and cannot become a controlling
requirement or close G1. A human specification owner must ratify the value in
the requirements traceability record and current spec hash.

## Literature Search And Extraction

For each paper/reference, extract:

- Node and supply.
- Coupling style: AC, DC, servo, direct ADC, mixed-signal.
- Area/channel and whether ADC is included.
- Power/channel and whether digital is included.
- Input-referred noise and integration band.
- Bandwidth and high-pass method.
- CMRR/PSRR and mismatch/measurement condition if available.
- Offset tolerance, input range, and backend architecture.
- Why it is or is not comparable.

Do not copy paper numbers without noting the measurement band and included
blocks.

## Architecture Matrix

Compare candidate architectures before choosing a transistor path:

| architecture | noise path | power | area | fHP/fLP control | backend load | CMFB/servo risk | pseudoR/well risk | evidence | decision |
|---|---|---|---|---|---|---|---|---|---|

Include local historical candidates even if they are not active. This prevents
the agent from re-opening a rejected path without a new reason.

## Architecture Candidate Nomination Criteria

Nominate an architecture for G2 review only if:

- It can plausibly meet the spec table.
- Its limiting loops and poles can be modeled.
- Primitive devices/passives can realize the required ranges.
- The required area/power is not obviously impossible.
- It has a clear first transistor-level experiment.

Keep a proposal as secondary if it is promising but needs a narrow cleanup.
Recommend rejection if it repeatedly needs trim-like behavior, unrealistic
passives, or unmodeled ideal blocks to pass. Record the disposition in a
decision record; only human authorization closes G2.
