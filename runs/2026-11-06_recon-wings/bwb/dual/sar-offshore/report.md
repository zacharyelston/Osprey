# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.7 km of track planned |
| Take-off mass | 1.57 kg (battery 0.25, shell 0.16, spar 0.022, fixed 1.14) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.5 |
| Root / tip chord | 44.1 / 12.4 cm (tip Re 153,219) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 18.3 m/s, 0.41, 9.0 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 78 W / 30 min |
| Mission time estimate (+20% reserve) | 25 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.77 | 0.42 | 34 / 56 | 90% | 11 |
| 2 | 0.60 | 1.57 | 0.25 | 33 / 54 | 90% | 11 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.3 min after launch |
| Pod reached | 90% (goal 90%); goal at 18.1 min |
| Time on task | 10.8 min |
| Search plan | 226 m track spacing, effective sweep width 688 m, 2 pattern pass(es) |
| Flight time / distance | 26.1 min / 23.4 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 75 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

