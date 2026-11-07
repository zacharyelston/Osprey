# Recon: one bird, many jobs (bwb airframe, gimbal payload)

Generated 2026-11-06 at unknown by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.31 kg, 1.00 m | ✗ 12% time on station | ✓ 37% | ✗ 52% POD | ✗ 89% POD | ✗ 18% POD | ✗ 21% area imaged | ✗ 17% area imaged |
| sar-datum | 1.32 kg, 1.00 m | ✗ 49% time on station | ✓ 54% | ✗ 62% POD | ✓ 18% | ✗ 38% POD | ✓ 15% | ✗ 81% area imaged |
| scout-anchorage | 1.33 kg, 1.00 m | ✗ 51% time on station | ✓ 55% | ✗ 62% POD | ✓ 19% | ✗ 40% POD | ✓ 17% | ✗ 84% area imaged |
| scout-island | 1.39 kg, 1.00 m | ✗ 69% time on station | ✓ 66% | ✗ 79% POD | ✓ 42% | ✗ 63% POD | ✓ 38% | ✓ 17% |
| sar-convoy | 1.48 kg, 1.00 m | ✗ 93% time on station | ✓ 76% | ✓ 17% | ✓ 61% | ✗ 79% POD | ✓ 54% | ✓ 39% |
| escort-flanks | 1.60 kg, 1.02 m | ✓ 17% | ✓ 82% | ✓ 41% | ✓ 71% | ✗ 87% POD | ✓ 65% | ✓ 54% |
| sar-offshore **(lightest that does everything)** | 2.11 kg, 1.32 m | ✓ 60% | ✓ 90% | ✓ 66% | ✓ 83% | ✓ 19% | ✓ 82% | ✓ 76% |
