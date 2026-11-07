# Water operations: sar-offshore, twinboom, gimbal

With the float kit (0.12 kg: planing shoe, seals, prop pylon), 2.85 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.44 (6.8 l sealed, 2.8 l displaced) | ✓ |
| Floating trim | level | -0.0° (nose up +), draft 7.3 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -13.3 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -11.5 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.45 W at 4.8 m/s (static thrust 18 N, T/W 0.65) | ✓ |
| Take-off run, calm water | | 18 m, 2.6 s, 0.35 Wh, lift-off at 13.7 m/s | |
| Waves for take-off (10% of the 50 cm shoe) | | H_s ≤ 5 cm: sea state 1 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 6.9 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 62% | ✓ 59% |
| inspect-vessel | ✓ 90% | ✓ 89% |
| sar-convoy | ✓ 61% | ✓ 59% |
| sar-datum | ✓ 81% | ✓ 79% |
| sar-offshore | ✓ 16% | ✗ 9% |
| scout-anchorage | ✓ 83% | ✓ 81% |
| scout-island | ✓ 76% | ✓ 74% |
