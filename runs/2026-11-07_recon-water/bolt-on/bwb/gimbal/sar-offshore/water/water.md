# Water operations: sar-offshore, bwb, gimbal

With the float kit (0.10 kg: planing shoe, seals, prop pylon), 2.21 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.73 (5.9 l sealed, 2.2 l displaced) | ✓ |
| Floating trim | level | -0.0° (nose up +), draft 2.6 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -12.5 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -8.7 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.64 W at 5.0 m/s (static thrust 18 N, T/W 0.83) | ✓ |
| Take-off run, calm water | | 14 m, 2.0 s, 0.26 Wh, lift-off at 14.1 m/s | |
| Waves for take-off (10% of the 44 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.9 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 60% | ✓ 54% |
| inspect-vessel | ✓ 90% | ✓ 89% |
| sar-convoy | ✓ 66% | ✓ 61% |
| sar-datum | ✓ 83% | ✓ 81% |
| sar-offshore | ✓ 19% | ✗ 7% |
| scout-anchorage | ✓ 82% | ✓ 79% |
| scout-island | ✓ 76% | ✓ 72% |
