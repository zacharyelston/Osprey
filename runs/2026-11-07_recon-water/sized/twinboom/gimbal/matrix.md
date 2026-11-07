# Recon: one bird, many jobs (twinboom airframe, gimbal payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.61 kg, 1.20 m | ✗ 24% time on station | ✓ 19% | ✗ 0% POD | ✗ 86% POD | ✗ 0% POD | ✗ 0% area imaged | ✗ 33% area imaged |
| scout-anchorage | 1.73 kg, 1.25 m | ✗ 50% time on station | ✓ 53% | ✗ 52% POD | ✓ 8% | ✗ 39% POD | ✓ 17% | ✗ 82% area imaged |
| sar-datum | 1.76 kg, 1.27 m | ✗ 57% time on station | ✓ 57% | ✗ 62% POD | ✓ 17% | ✗ 46% POD | ✓ 24% | ✗ 92% area imaged |
| scout-island | 1.84 kg, 1.33 m | ✗ 68% time on station | ✓ 66% | ✗ 76% POD | ✓ 34% | ✗ 63% POD | ✓ 40% | ✓ 17% |
| sar-convoy | 2.08 kg, 1.50 m | ✓ 13% | ✓ 78% | ✓ 17% | ✓ 57% | ✗ 81% POD | ✓ 61% | ✓ 46% |
| escort-flanks | 2.12 kg, 1.53 m | ✓ 17% | ✓ 79% | ✓ 21% | ✓ 60% | ✗ 82% POD | ✓ 63% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 3.01 kg, 2.27 m | ✓ 62% | ✓ 90% | ✓ 61% | ✓ 81% | ✓ 15% | ✓ 83% | ✓ 77% |
