# Recon: one bird, many jobs (gimbal payload)

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.47 kg, 1.20 m | ✗ 16% time on station | ✓ 23% | ✗ 0% POD | ✗ 87% POD | ✗ 0% POD | ✗ 5% area imaged | ✗ 28% area imaged |
| scout-anchorage | 1.58 kg, 1.20 m | ✗ 51% time on station | ✓ 53% | ✗ 52% POD | ✓ 9% | ✗ 39% POD | ✓ 17% | ✗ 82% area imaged |
| sar-datum | 1.60 kg, 1.20 m | ✗ 58% time on station | ✓ 57% | ✗ 62% POD | ✓ 17% | ✗ 46% POD | ✓ 24% | ✗ 92% area imaged |
| scout-island | 1.67 kg, 1.21 m | ✗ 68% time on station | ✓ 66% | ✗ 79% POD | ✓ 33% | ✗ 63% POD | ✓ 39% | ✓ 17% |
| sar-convoy | 1.87 kg, 1.36 m | ✓ 11% | ✓ 77% | ✓ 15% | ✓ 56% | ✗ 81% POD | ✓ 60% | ✓ 46% |
| escort-flanks | 1.92 kg, 1.39 m | ✓ 17% | ✓ 79% | ✓ 20% | ✓ 59% | ✗ 82% POD | ✓ 63% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 2.73 kg, 2.02 m | ✓ 62% | ✓ 90% | ✓ 61% | ✓ 81% | ✓ 16% | ✓ 83% | ✓ 76% |
