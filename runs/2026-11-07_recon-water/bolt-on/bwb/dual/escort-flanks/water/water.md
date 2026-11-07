# Water operations: escort-flanks, bwb, dual

With the float kit (0.10 kg: planing shoe, seals, prop pylon), 1.90 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.71 (5.0 l sealed, 1.9 l displaced) | ✓ |
| Floating trim | level | -0.2° (nose up +), draft 2.7 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -12.5 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -7.6 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.77 W at 5.0 m/s (static thrust 18 N, T/W 0.97) | ✓ |
| Take-off run, calm water | | 12 m, 1.7 s, 0.22 Wh, lift-off at 14.2 m/s | |
| Waves for take-off (10% of the 44 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 8.4 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 15% | ✗ 2% |
| inspect-vessel | ✓ 81% | ✓ 78% |
| sar-convoy | ✓ 65% | ✓ 60% |
| sar-datum | ✓ 89% | ✓ 87% |
| sar-offshore | ✓ 53% | ✓ 46% |
| scout-anchorage | ✓ 69% | ✓ 65% |
| scout-island | ✓ 71% | ✓ 67% |
