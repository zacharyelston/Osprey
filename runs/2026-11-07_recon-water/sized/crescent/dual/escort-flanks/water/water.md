# Water operations: escort-flanks, crescent, dual

With the float kit (0.14 kg: planing shoe, seals, prop pylon), 2.05 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 1.74 (3.5 l sealed, 2.0 l displaced) | ✗ |
| Floating trim | level | +15.6° (nose up +), draft 6.9 cm | ✗ |
| Prop tips above the water, afloat | ≥ 5 cm | -18.6 cm: needs a 24 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -3.0 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.70 W at 4.9 m/s (static thrust 18 N, T/W 0.89) | ✓ |
| Take-off run, calm water | | 13 m, 1.8 s, 0.24 Wh, lift-off at 13.8 m/s | |
| Waves for take-off (10% of the 42 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.7 g | ✗ |

Every job, sized with the kit aboard: battery left on landing. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | With the kit |
|---|---|
| escort-flanks | ✓ 17% |
| inspect-vessel | ✓ 78% |
| sar-convoy | ✓ 58% |
| sar-datum | ✓ 88% |
| sar-offshore | ✓ 49% |
| scout-anchorage | ✓ 68% |
| scout-island | ✓ 69% |
