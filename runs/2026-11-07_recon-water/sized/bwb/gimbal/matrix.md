# Recon: one bird, many jobs (bwb airframe, gimbal payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.41 kg, 1.00 m | ✗ 11% time on station | ✓ 30% | ✗ 5% POD | ✗ 90% POD | ✗ 0% POD | ✗ 15% area imaged | ✗ 16% area imaged |
| sar-datum | 1.45 kg, 1.00 m | ✗ 44% time on station | ✓ 52% | ✗ 60% POD | ✓ 16% | ✗ 33% POD | ✓ 12% | ✗ 77% area imaged |
| scout-anchorage | 1.46 kg, 1.00 m | ✗ 50% time on station | ✓ 55% | ✗ 63% POD | ✓ 22% | ✗ 40% POD | ✓ 17% | ✗ 84% area imaged |
| scout-island | 1.54 kg, 1.00 m | ✗ 66% time on station | ✓ 67% | ✗ 81% POD | ✓ 45% | ✗ 64% POD | ✓ 39% | ✓ 16% |
| sar-convoy | 1.66 kg, 1.06 m | ✗ 99% time on station | ✓ 77% | ✓ 19% | ✓ 61% | ✗ 80% POD | ✓ 57% | ✓ 41% |
| escort-flanks | 1.74 kg, 1.11 m | ✓ 15% | ✓ 80% | ✓ 29% | ✓ 66% | ✗ 84% POD | ✓ 63% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 2.38 kg, 1.48 m | ✓ 61% | ✓ 90% | ✓ 65% | ✓ 81% | ✓ 18% | ✓ 82% | ✓ 76% |
