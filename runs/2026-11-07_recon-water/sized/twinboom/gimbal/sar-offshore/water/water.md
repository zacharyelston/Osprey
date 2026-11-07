# Water operations: sar-offshore, twinboom, gimbal

With the float kit (0.12 kg: planing shoe, seals, prop pylon), 3.01 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.50 (7.3 l sealed, 2.9 l displaced) | ✓ |
| Floating trim | level | -0.3° (nose up +), draft 7.6 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -13.4 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -11.8 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.41 W at 4.7 m/s (static thrust 18 N, T/W 0.61) | ✓ |
| Take-off run, calm water | | 18 m, 2.7 s, 0.36 Wh, lift-off at 13.2 m/s | |
| Waves for take-off (10% of the 50 cm shoe) | | H_s ≤ 5 cm: sea state 1 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 6.3 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 62% |
| inspect-vessel | ✓ 90% |
| sar-convoy | ✓ 61% |
| sar-datum | ✓ 81% |
| sar-offshore | ✓ 15% |
| scout-anchorage | ✓ 83% |
| scout-island | ✓ 77% |
