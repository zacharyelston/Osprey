# Water operations: escort-flanks, twinboom, dual

With the float kit (0.12 kg: planing shoe, seals, prop pylon), 2.33 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.65 (6.0 l sealed, 2.3 l displaced) | ✓ |
| Floating trim | level | +0.9° (nose up +), draft 6.4 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -13.0 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -8.1 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.59 W at 4.8 m/s (static thrust 18 N, T/W 0.79) | ✓ |
| Take-off run, calm water | | 15 m, 2.1 s, 0.28 Wh, lift-off at 13.8 m/s | |
| Waves for take-off (10% of the 50 cm shoe) | | H_s ≤ 5 cm: sea state 1 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.4 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 17% |
| inspect-vessel | ✓ 79% |
| sar-convoy | ✓ 57% |
| sar-datum | ✓ 89% |
| sar-offshore | ✓ 50% |
| scout-anchorage | ✓ 69% |
| scout-island | ✓ 70% |
