# Handoff Template

Use this as a compact final handoff shape.

```markdown
# Current Thread Handoff - YYYY-MM-DD - <Candidate Or Phase>

## Current Phase

- Phase: spec / literature / architecture / primitive tables / behavioral model / block implementation / full-chain / variation / layout / tapeout-candidate / post-layout / signoff
- Active objective:
- Latest user request:
- Source handoffs used:

## Specifications

| metric | preferred | acceptable | current evidence | status |
|---|---:|---:|---|---|
| Gain | | | | |
| Noise | | | | |
| Power | | | | |
| Area | | | | |
| fHP/fLP | | | | |
| CMRR/PSRR | | | | |
| Input/backend interface | | | | |

## Architecture State

| architecture | status | evidence | reason |
|---|---|---|---|
| | active | | |
| | fallback | | |
| | rejected | | |

## Current Topology

- Stage-1:
- Stage-1 Cin/Cf:
- Stage-1 pseudoR/well-bias:
- Interstage LPF:
- Stage-2:
- Stage-2 pseudoR/well-bias:
- Stage-2 CMFB:
- Output/MUX/ADC proxy:

## Models And Tables

- Literature comparison:
- Primitive/device tables:
- Behavioral/system models:
- Measured-port models:
- Model limitations:

## Latest Passed Gates

| gate | status | report |
|---|---:|---|
| Module DC/PVT | | |
| Module AC/noise/rejection | | |
| Module reports/images | | |
| Full-chain DC/PVT/noise/rejection | | |
| Mismatch-aware CMRR/PSRR | | |
| STB/startup | | |
| MC | | |
| Tapeout readiness audit | | |
| PEX/post-layout | | |

## Key Metrics

- Full-chain power:
- Gain at 1 kHz:
- Noise 300 Hz to 10 kHz:
- fHP:
- fLP:
- Mismatch-aware CMRR:
- Mismatch-aware VDD PSRR:
- Output offset / CM:
- Area basis and area/ch:
- Layout/floorplan suggestion:

## Tapeout Readiness

- Device sizing audit:
- Reliability/voltage-domain audit:
- Precision cap/resistor/pseudoR layout risk:
- High-Z node audit:
- Bias/reference implementation plan:
- Startup/reset/recovery evidence:
- CMRR/PSRR evidence tier: nominal / deterministic mismatch / PEX+MC
- Parasitic stress / PEX plan:
- Test/trim/calibration hooks:
- ESD/pad/top-level interface plan:
- DFM/open layout risks:

## Important Files

- Netlist:
- Script:
- Report:
- Module reports:
- Module result images:
- Curves:
- Plots:
- Area/comparison:
- Floorplan image:

## Decisions

- Branch closure:
  - Gates passed:
  - Functional ideal elements:
  - Worst corner and reason:
  - Limiting mechanism:
  - Continue sizing sweep, topology/root-cause branch, or promote:
  - Metrics improved / worsened:
  - Candidate status:
  - Next smallest discriminating experiment:
- Accepted:
- Rejected:
- Open risks:

## Next Step

1. <one concrete next action>
```
