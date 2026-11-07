# Recon: one bird, many jobs (tailsitter airframe, dual payload)

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| sar-datum | 1.61 kg, 1.00 m | ✗ 8% time on station | ✗ 68% orbit done | ✗ 0% POD | ✓ 42% | ✗ 0% POD | ✗ 0% area imaged | ✗ 21% area imaged |
| inspect-vessel | 1.63 kg, 1.04 m | ✗ 22% time on station | ✓ 17% | ✗ 0% POD | ✓ 54% | ✗ 0% POD | ✗ 0% area imaged | ✗ 67% area imaged |
| scout-island | 1.72 kg, 1.10 m | ✗ 38% time on station | ✓ 44% | ✗ 61% POD | ✓ 69% | ✗ 0% POD | ✓ 14% | ✓ 17% |
| scout-anchorage | 1.72 kg, 1.10 m | ✗ 40% time on station | ✓ 46% | ✗ 65% POD | ✓ 70% | ✗ 4% POD | ✓ 17% | ✓ 20% |
| sar-convoy | 1.79 kg, 1.14 m | ✗ 50% time on station | ✓ 56% | ✓ 17% | ✓ 75% | ✗ 84% POD | ✓ 31% | ✓ 34% |
| sar-offshore | 1.90 kg, 1.21 m | ✗ 63% time on station | ✓ 66% | ✓ 35% | ✓ 81% | ✓ 17% | ✓ 47% | ✓ 49% |
| escort-flanks **(lightest that does everything)** | 2.22 kg, 1.40 m | ✓ 17% | ✓ 79% | ✓ 60% | ✓ 88% | ✓ 50% | ✓ 68% | ✓ 69% |
