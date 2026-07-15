# Pseudo-Resistor And Well-Bias Notes

This is technical guidance, not gate state. The numeric first-pass values below
are historical examples and must be replaced or explicitly adopted by the
approved project/PDK overlay before they control evidence evaluation.

## Core Mental Model

For pseudo-resistor leakage compensation, the well-bias path should usually make
DNW slowly track the relevant PWELL/local well potential. It is not necessarily
a wideband buffer. The key design question is the required DC tracking,
bandwidth, output impedance, PSRR, area, and manufacturability.

## Terminal Mapping

Check every pseudoR wrapper:

- `PSUB`: p-substrate. Usually connect to ground.
- `DNW`: deep n-well. Drive from well-bias output or use an explicit diagnostic
  tie such as VDD only when testing.
- `PWELL`: internal p-well node. It may need to connect to the well-bias input,
  not ground.
- `A`, `B`: two signal terminals. PEX pin order may be `B A`; wrappers should
  normalize this and document the mapping.

## Driver Strategy

Reasonable candidate types:

- Simple low-power MOS follower/OTA with explicit current mirror bias.
- Slow outer servo that sets a command voltage plus a local low-Z driver.
- Shared-side driver only when mismatch/headroom/fHP results justify sharing.

Avoid promoting:

- Ideal VCVS or behavioral drivers as final circuits.
- Large passive caps or huge resistors without area/PVT audit.
- Very tiny bias currents that look good in simulation but create manufacturing
  risk.
- Wideband unity followers from PWELL to DNW unless transient evidence shows
  they are required and harmless.
- Shared DNW/PWELL across pseudoR series cells while leakage scaling is under
  test.
- Naked high-Z OTA outputs connected directly to DNW.

## First-Pass Targets

- PWELL to DNW tracking bandwidth: `1-10 Hz` nominal.
- Acceptable first-pass range: `1-100 Hz`.
- Avoid `>=1 kHz` unless proven harmless.
- Systematic tracking offset preferably `<=0.3-0.5 mV`.
- DNW output impedance should be low enough in the signal band.
- Use independent DNW/PWELL per pseudoR segment if series scaling is required.

## Design Flow

1. Use ideal or behavioral models to set required bandwidth and Rout.
2. Map the requirement to a MOS-only or mostly-MOS circuit.
3. Verify standalone PVT.
4. Insert in the module and verify DC/noise/rejection.
5. Insert in full-chain only after module gates pass.
6. Run mismatch smoke before MC.

## Known Lessons

- Wider/larger driver devices can improve mismatch but increase area and
  capacitance.
- pseudoR2 with fewer cells can reduce pseudoR cell count, but larger per-cell
  16x drivers may offset the area saving.
- Stage-2 fHP is often sensitive to pseudoR leakage and well-bias topology.
- If a no-driver diagnostic works, do not assume it is manufacturable until
  PWELL/DNW biasing and leakage paths are physically realizable.
- If pseudoR series count does not scale fHP, the dominant leakage path is not
  necessarily the A-B channel resistance; inspect endpoint, well, DNW, and PSUB
  leakage.
