# Water operations: sar-offshore, crescent, gimbal

With the float kit (0.14 kg: planing shoe, seals, prop pylon), 2.32 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 1.59 (3.6 l sealed, 2.3 l displaced) | ✗ |
| Floating trim | level | +13.7° (nose up +), draft 5.7 cm | ✗ |
| Prop tips above the water, afloat | ≥ 5 cm | -14.9 cm: needs a 20 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -3.0 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.60 W at 5.0 m/s (static thrust 18 N, T/W 0.79) | ✓ |
| Take-off run, calm water | | 15 m, 2.1 s, 0.28 Wh, lift-off at 14.2 m/s | |
| Waves for take-off (10% of the 42 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.9 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 61% | ✓ 57% |
| inspect-vessel | ✓ 90% | ✓ 89% |
| sar-convoy | ✓ 64% | ✓ 59% |
| sar-datum | ✓ 81% | ✓ 79% |
| sar-offshore | ✓ 18% | ✗ 7% |
| scout-anchorage | ✓ 83% | ✓ 80% |
| scout-island | ✓ 76% | ✓ 73% |
