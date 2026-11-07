# Recon: one bird, many jobs (bwb airframe, dual payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| sar-datum | 1.57 kg, 1.00 m | ✗ 10% time on station | ✓ 22% | ✗ 0% POD | ✓ 57% | ✗ 0% POD | ✗ 6% area imaged | ✗ 29% area imaged |
| inspect-vessel | 1.57 kg, 1.00 m | ✗ 11% time on station | ✓ 26% | ✗ 0% POD | ✓ 59% | ✗ 0% POD | ✗ 5% area imaged | ✗ 37% area imaged |
| scout-island | 1.60 kg, 1.02 m | ✗ 37% time on station | ✓ 45% | ✗ 68% POD | ✓ 69% | ✗ 0% POD | ✓ 13% | ✓ 17% |
| scout-anchorage | 1.61 kg, 1.03 m | ✗ 38% time on station | ✓ 48% | ✗ 90% POD | ✓ 70% | ✗ 33% POD | ✓ 17% | ✓ 21% |
| sar-convoy | 1.64 kg, 1.05 m | ✗ 46% time on station | ✓ 54% | ✓ 17% | ✓ 74% | ✗ 71% POD | ✓ 28% | ✓ 31% |
| sar-offshore | 1.73 kg, 1.10 m | ✗ 62% time on station | ✓ 66% | ✓ 37% | ✓ 81% | ✓ 17% | ✓ 46% | ✓ 49% |
| escort-flanks **(lightest that does everything)** | 1.97 kg, 1.25 m | ✓ 16% | ✓ 80% | ✓ 63% | ✓ 88% | ✓ 51% | ✓ 69% | ✓ 70% |
