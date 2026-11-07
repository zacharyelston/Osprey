# Recon: one bird, many jobs (dual payload)

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| sar-datum | 1.65 kg, 1.20 m | ✗ 15% time on station | ✓ 17% | ✗ 0% POD | ✓ 55% | ✗ 0% POD | ✗ 0% area imaged | ✗ 57% area imaged |
| inspect-vessel | 1.65 kg, 1.20 m | ✗ 18% time on station | ✓ 19% | ✗ 0% POD | ✓ 56% | ✗ 0% POD | ✗ 0% area imaged | ✗ 64% area imaged |
| scout-island | 1.71 kg, 1.24 m | ✗ 41% time on station | ✓ 42% | ✗ 0% POD | ✓ 69% | ✗ 0% POD | ✓ 14% | ✓ 17% |
| scout-anchorage | 1.72 kg, 1.24 m | ✗ 42% time on station | ✓ 44% | ✗ 55% POD | ✓ 70% | ✗ 0% POD | ✓ 17% | ✓ 19% |
| sar-convoy | 1.80 kg, 1.30 m | ✗ 59% time on station | ✓ 58% | ✓ 17% | ✓ 77% | ✗ 88% POD | ✓ 37% | ✓ 39% |
| sar-offshore | 1.87 kg, 1.35 m | ✗ 67% time on station | ✓ 65% | ✓ 29% | ✓ 81% | ✓ 17% | ✓ 48% | ✓ 50% |
| escort-flanks **(lightest that does everything)** | 2.13 kg, 1.54 m | ✓ 17% | ✓ 79% | ✓ 57% | ✓ 89% | ✓ 50% | ✓ 69% | ✓ 69% |
