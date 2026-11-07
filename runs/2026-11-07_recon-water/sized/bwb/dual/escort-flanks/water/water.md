# Water operations: escort-flanks, bwb, dual

With the float kit (0.10 kg: planing shoe, seals, prop pylon), 1.97 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.86 (5.5 l sealed, 1.9 l displaced) | ✓ |
| Floating trim | level | -0.4° (nose up +), draft 2.7 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -12.3 cm: needs a 17 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -7.5 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.74 W at 4.9 m/s (static thrust 18 N, T/W 0.93) | ✓ |
| Take-off run, calm water | | 12 m, 1.7 s, 0.22 Wh, lift-off at 13.8 m/s | |
| Waves for take-off (10% of the 44 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.9 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 16% |
| inspect-vessel | ✓ 80% |
| sar-convoy | ✓ 63% |
| sar-datum | ✓ 88% |
| sar-offshore | ✓ 51% |
| scout-anchorage | ✓ 69% |
| scout-island | ✓ 70% |
