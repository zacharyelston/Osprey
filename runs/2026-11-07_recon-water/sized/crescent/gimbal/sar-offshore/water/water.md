# Water operations: sar-offshore, crescent, gimbal

With the float kit (0.14 kg: planing shoe, seals, prop pylon), 2.51 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 1.64 (4.0 l sealed, 2.4 l displaced) | ✗ |
| Floating trim | level | +12.4° (nose up +), draft 5.2 cm | ✗ |
| Prop tips above the water, afloat | ≥ 5 cm | -14.2 cm: needs a 19 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -3.1 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.54 W at 4.9 m/s (static thrust 18 N, T/W 0.73) | ✓ |
| Take-off run, calm water | | 16 m, 2.3 s, 0.30 Wh, lift-off at 13.8 m/s | |
| Waves for take-off (10% of the 42 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.2 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 61% |
| inspect-vessel | ✓ 90% |
| sar-convoy | ✓ 63% |
| sar-datum | ✓ 81% |
| sar-offshore | ✓ 18% |
| scout-anchorage | ✓ 83% |
| scout-island | ✓ 76% |
