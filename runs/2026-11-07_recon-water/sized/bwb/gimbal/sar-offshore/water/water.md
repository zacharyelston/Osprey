# Water operations: sar-offshore, bwb, gimbal

With the float kit (0.10 kg: planing shoe, seals, prop pylon), 2.38 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.86 (6.7 l sealed, 2.3 l displaced) | ✓ |
| Floating trim | level | -0.3° (nose up +), draft 2.6 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -12.4 cm: needs a 17 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -8.6 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.58 W at 4.8 m/s (static thrust 18 N, T/W 0.77) | ✓ |
| Take-off run, calm water | | 15 m, 2.1 s, 0.28 Wh, lift-off at 13.8 m/s | |
| Waves for take-off (10% of the 44 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.4 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 61% |
| inspect-vessel | ✓ 90% |
| sar-convoy | ✓ 65% |
| sar-datum | ✓ 81% |
| sar-offshore | ✓ 18% |
| scout-anchorage | ✓ 82% |
| scout-island | ✓ 76% |
