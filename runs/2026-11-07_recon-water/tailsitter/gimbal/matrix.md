# Recon: one bird, many jobs (tailsitter airframe, gimbal payload)

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.44 kg, 1.00 m | ✗ 19% time on station | ✓ 18% | ✗ 0% POD | ✗ 87% POD | ✗ 0% POD | ✗ 0% area imaged | ✗ 31% area imaged |
| sar-datum | 1.53 kg, 1.00 m | ✗ 41% time on station | ✓ 50% | ✗ 51% POD | ✓ 16% | ✗ 27% POD | ✓ 8% | ✗ 71% area imaged |
| scout-anchorage | 1.56 kg, 1.00 m | ✗ 48% time on station | ✓ 54% | ✗ 66% POD | ✓ 24% | ✗ 40% POD | ✓ 17% | ✗ 82% area imaged |
| scout-island | 1.68 kg, 1.09 m | ✗ 67% time on station | ✓ 67% | ✗ 80% POD | ✓ 43% | ✗ 64% POD | ✓ 40% | ✓ 17% |
| sar-convoy | 1.89 kg, 1.20 m | ✓ 5% | ✓ 77% | ✓ 17% | ✓ 60% | ✗ 79% POD | ✓ 58% | ✓ 43% |
| escort-flanks | 1.98 kg, 1.25 m | ✓ 16% | ✓ 79% | ✓ 26% | ✓ 65% | ✗ 83% POD | ✓ 63% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 2.96 kg, 1.81 m | ✓ 61% | ✓ 90% | ✓ 64% | ✓ 81% | ✓ 17% | ✓ 82% | ✓ 76% |
