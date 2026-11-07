# Recon: one bird, many jobs (crescent airframe, dual payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| sar-datum | 1.69 kg, 1.40 m | ✗ 15% time on station | ✓ 28% | ✗ 0% POD | ✓ 61% | ✗ 0% POD | ✗ 35% area imaged | ✗ 63% area imaged |
| inspect-vessel | 1.69 kg, 1.40 m | ✗ 24% time on station | ✓ 32% | ✗ 0% POD | ✓ 63% | ✗ 0% POD | ✗ 53% area imaged | ✗ 84% area imaged |
| scout-island | 1.71 kg, 1.42 m | ✗ 41% time on station | ✓ 42% | ✗ 0% POD | ✓ 68% | ✗ 0% POD | ✓ 13% | ✓ 17% |
| scout-anchorage | 1.72 kg, 1.44 m | ✗ 42% time on station | ✓ 44% | ✗ 58% POD | ✓ 69% | ✗ 0% POD | ✓ 16% | ✓ 19% |
| sar-convoy | 1.77 kg, 1.55 m | ✗ 58% time on station | ✓ 57% | ✓ 15% | ✓ 76% | ✗ 85% POD | ✓ 36% | ✓ 38% |
| sar-offshore | 1.84 kg, 1.63 m | ✗ 67% time on station | ✓ 65% | ✓ 31% | ✓ 81% | ✓ 17% | ✓ 48% | ✓ 49% |
| escort-flanks **(lightest that does everything)** | 2.05 kg, 1.87 m | ✓ 17% | ✓ 78% | ✓ 58% | ✓ 88% | ✓ 49% | ✓ 68% | ✓ 69% |
