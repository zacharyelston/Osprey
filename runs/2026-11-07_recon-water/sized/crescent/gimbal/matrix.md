# Recon: one bird, many jobs (crescent airframe, gimbal payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.51 kg, 1.40 m | ✗ 18% time on station | ✓ 34% | ✗ 0% POD | ✓ 20% | ✗ 0% POD | ✗ 27% area imaged | ✗ 27% area imaged |
| scout-anchorage | 1.55 kg, 1.41 m | ✗ 50% time on station | ✓ 52% | ✗ 53% POD | ✓ 9% | ✗ 39% POD | ✓ 16% | ✗ 82% area imaged |
| sar-datum | 1.57 kg, 1.45 m | ✗ 58% time on station | ✓ 57% | ✗ 63% POD | ✓ 17% | ✗ 46% POD | ✓ 24% | ✗ 92% area imaged |
| scout-island | 1.63 kg, 1.54 m | ✗ 68% time on station | ✓ 65% | ✗ 79% POD | ✓ 34% | ✗ 63% POD | ✓ 39% | ✓ 17% |
| sar-convoy | 1.80 kg, 1.70 m | ✓ 11% | ✓ 77% | ✓ 17% | ✓ 57% | ✗ 81% POD | ✓ 60% | ✓ 46% |
| escort-flanks | 1.83 kg, 1.73 m | ✓ 17% | ✓ 79% | ✓ 22% | ✓ 59% | ✗ 82% POD | ✓ 63% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 2.51 kg, 2.20 m | ✓ 61% | ✓ 90% | ✓ 63% | ✓ 81% | ✓ 18% | ✓ 83% | ✓ 76% |
