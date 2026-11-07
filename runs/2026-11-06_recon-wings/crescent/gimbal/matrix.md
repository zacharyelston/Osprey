# Recon: one bird, many jobs (crescent airframe, gimbal payload)

Generated 2026-11-06 at unknown by `uv run osprey recon --mission all`. Each row is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is ✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it got).

| Airframe sized for | Mass, span | escort-flanks | inspect-vessel | sar-convoy | sar-datum | sar-offshore | scout-anchorage | scout-island |
|---|---|---|---|---|---|---|---|---|
| inspect-vessel | 1.37 kg, 1.40 m | ✗ 10% time on station | ✓ 30% | ✗ 30% POD | ✗ 87% POD | ✗ 12% POD | ✗ 18% area imaged | ✗ 15% area imaged |
| scout-anchorage | 1.38 kg, 1.40 m | ✗ 53% time on station | ✓ 52% | ✗ 54% POD | ✓ 9% | ✗ 34% POD | ✓ 17% | ✗ 83% area imaged |
| sar-datum | 1.39 kg, 1.40 m | ✗ 60% time on station | ✓ 56% | ✗ 62% POD | ✓ 17% | ✗ 45% POD | ✓ 24% | ✗ 92% area imaged |
| scout-island | 1.44 kg, 1.40 m | ✗ 69% time on station | ✓ 65% | ✗ 79% POD | ✓ 33% | ✗ 63% POD | ✓ 39% | ✓ 17% |
| sar-convoy | 1.56 kg, 1.48 m | ✓ 8% | ✓ 76% | ✓ 14% | ✓ 55% | ✗ 79% POD | ✓ 58% | ✓ 43% |
| escort-flanks | 1.60 kg, 1.52 m | ✓ 17% | ✓ 78% | ✓ 22% | ✓ 59% | ✗ 82% POD | ✓ 62% | ✓ 49% |
| sar-offshore **(lightest that does everything)** | 2.18 kg, 1.98 m | ✓ 61% | ✓ 90% | ✓ 64% | ✓ 81% | ✓ 18% | ✓ 83% | ✓ 76% |
