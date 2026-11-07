# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.7 km of track planned |
| Take-off mass | 1.73 kg (battery 0.28, shell 0.18, spar 0.023, fixed 1.24) |
| Span / area / aspect ratio | 1.10 m / 0.202 m² / 6.0 |
| Root / tip chord | 44.1 / 12.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.9 m/s, 0.43, 8.3 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 87 W / 31 min |
| Mission time estimate (+20% reserve) | 26 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.96 | 0.49 | 39 / 65 | 90% | 12 |
| 2 | 0.59 | 1.73 | 0.28 | 38 / 63 | 90% | 11 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.3 min after launch |
| Pod reached | 90% (goal 90%); goal at 18.5 min |
| Time on task | 11.2 min |
| Search plan | 226 m track spacing, effective sweep width 688 m, 2 pattern pass(es) |
| Flight time / distance | 26.8 min / 23.3 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 84 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

