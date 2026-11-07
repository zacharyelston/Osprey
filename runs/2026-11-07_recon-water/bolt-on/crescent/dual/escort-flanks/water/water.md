# Water operations: escort-flanks, crescent, dual

With the float kit (0.14 kg: planing shoe, seals, prop pylon), 1.97 kg in all. REF inputs in `[water]` of `design/recon/airframe.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Reserve buoyancy (sealed volume / displaced) | ≥ 2.0 | 1.69 (3.2 l sealed, 1.9 l displaced) | ✗ |
| Floating trim | level | +17.8° (nose up +), draft 6.8 cm | ✗ |
| Prop tips above the water, afloat | ≥ 5 cm | -18.2 cm: needs a 23 cm pylon | ✗ |
| Cameras out of the water, afloat | > 0 | -3.5 cm | ✗ |
| Thrust margin over the hump | ≥ 0.10 W | 0.74 W at 5.1 m/s (static thrust 18 N, T/W 0.93) | ✓ |
| Take-off run, calm water | | 13 m, 1.8 s, 0.23 Wh, lift-off at 14.3 m/s | |
| Waves for take-off (10% of the 42 cm shoe) | | H_s ≤ 4 cm: sea state 0 | |
| Landing load factor (FAR 23.527, 20° deadrise) | ≤ 3.0 g (sized for) | 8.5 g | ✗ |

Every job again, carrying the kit: battery left on landing, without the kit and with it. The missions keep a 20 % energy reserve, about 17% of the battery at landing; ✗ marks a job that fails or lands into it.

| Job | Bare | With the kit |
|---|---|---|
| escort-flanks | ✓ 17% | ✗ 6% |
| inspect-vessel | ✓ 79% | ✓ 76% |
| sar-convoy | ✓ 60% | ✓ 53% |
| sar-datum | ✓ 88% | ✓ 87% |
| sar-offshore | ✓ 49% | ✓ 42% |
| scout-anchorage | ✓ 68% | ✓ 64% |
| scout-island | ✓ 69% | ✓ 65% |
