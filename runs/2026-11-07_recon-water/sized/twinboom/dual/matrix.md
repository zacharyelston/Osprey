# Recon: one bird, many jobs (twinboom airframe, dual payload)

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| sar-datum | 1.78 kg, 1.20 m | ✗ 14% time on station | ✓ 8% | ✗ 0% POD | ✓ 50% | ✗ 0% POD | ✗ 0% area imaged | ✗ 48% area imaged |
| inspect-vessel | 1.79 kg, 1.25 m | ✗ 26% time on station | ✓ 17% | ✗ 0% POD | ✓ 56% | ✗ 0% POD | ✗ 0% area imaged | ✗ 73% area imaged |
| scout-island | 1.87 kg, 1.35 m | ✗ 41% time on station | ✓ 43% | ✗ 0% POD | ✓ 69% | ✗ 0% POD | ✓ 15% | ✓ 17% |
| scout-anchorage | 1.87 kg, 1.36 m | ✗ 41% time on station | ✓ 44% | ✗ 0% POD | ✓ 70% | ✗ 0% POD | ✓ 17% | ✓ 19% |
| sar-convoy | 1.97 kg, 1.42 m | ✗ 60% time on station | ✓ 59% | ✓ 17% | ✓ 78% | ✗ 89% POD | ✓ 39% | ✓ 40% |
| sar-offshore | 2.04 kg, 1.47 m | ✗ 67% time on station | ✓ 65% | ✓ 30% | ✓ 81% | ✓ 17% | ✓ 48% | ✓ 50% |
| escort-flanks **(lightest that does everything)** | 2.33 kg, 1.69 m | ✓ 17% | ✓ 79% | ✓ 57% | ✓ 89% | ✓ 50% | ✓ 69% | ✓ 70% |
