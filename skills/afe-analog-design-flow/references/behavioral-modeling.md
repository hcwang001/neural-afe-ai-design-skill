# Behavioral Modeling

Behavioral output is G2/G4 evidence and may guide transistor work, but it cannot
satisfy G5-or-later transistor, PEX, post-layout, or release artifacts. Every
model must record assumptions, source/spec hash, revision, applicability, and
planned correlation.

## Role

Behavioral models are used to set requirements and compare architectures before
expensive transistor-level iteration. They are not final proof.

## Required Model Types

### Full-Chain Budget Model

Use for:

- Gain allocation.
- Noise contribution and referral.
- Loading and bandwidth allocation.
- Power and area budgets.
- High-pass and low-pass target ranges.

### Loop/Plant Model

Use for:

- CMFB loop requirements.
- Well-bias driver bandwidth and output impedance.
- Servo loops.
- Compensation and backend loading interactions.

Include plant gain, control-node poles, output poles, actuator authority,
headroom, and common-mode range. A model that omits the failure mechanism cannot
justify a circuit decision.

### Measured-Port Model

Once transistor data exists, prefer measured-port models over standalone ideal
models. Extract:

- Output resistance or effective plant gain.
- Dominant poles at output and control nodes.
- Next-stage load.
- Control-path gain and phase.
- Bias/current variation across PVT.

Use measured-port results to set the next transistor-level target.

## Modeling Workflow

1. Build a simple chain budget to choose architecture.
2. Build focused loop models for the riskiest loops.
3. Run small transistor probes to measure missing plant parameters.
4. Update the behavioral model with measured ports.
5. Use the updated model to choose a small number of transistor candidates.

## Red Flags

- A standalone model passes but integrated transistor simulation fails.
- The model uses ideal resistors/caps/VCVS blocks without mapping them to
  physical devices.
- A loop target is chosen because it is easy to simulate, not because the
  system needs it.
- A dense sweep keeps changing numbers but not the underlying failure.

## Historical Lesson

In the prior AFE work, early behavior models were useful for gain/noise/loading
budgets, but they did not capture transistor-level CMFB offset, headroom, and
high common-mode plant gain. Later measured-port/co-design models were more
useful because they included the integrated plant.
