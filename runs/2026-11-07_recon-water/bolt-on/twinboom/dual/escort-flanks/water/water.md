# Water operations: escort-flanks, twinboom, dual

With the float kit (0.12 kg: planing shoe, seals, prop pylon), 2.25 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 2.63 (5.8 l sealed, 2.2 l displaced) | ✓ |
| Floating trim | level | +1.5° (nose up +), draft 6.2 cm | ✓ |
| Prop tips above the water, afloat | ≥ 5 cm | -13.2 cm: needs a 18 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -8.0 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.61 W at 5.0 m/s (static thrust 18 N, T/W 0.82) | ✓ |
| Take-off run, calm water | | 15 m, 2.1 s, 0.27 Wh, lift-off at 14.2 m/s | |
| Waves for take-off (10% of the 50 cm shoe) | | H_s ≤ 5 cm: sea state 1 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 7.9 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 17% | ✗ 9% |
| inspect-vessel | ✓ 79% | ✓ 77% |
| sar-convoy | ✓ 57% | ✓ 54% |
| sar-datum | ✓ 89% | ✓ 87% |
| sar-offshore | ✓ 50% | ✓ 45% |
| scout-anchorage | ✓ 69% | ✓ 65% |
| scout-island | ✓ 69% | ✓ 67% |
