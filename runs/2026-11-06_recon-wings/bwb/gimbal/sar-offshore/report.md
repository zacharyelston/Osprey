# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 63.8 km of track planned |
| Take-off mass | 2.11 kg (battery 0.88, shell 0.22, spar 0.034, fixed 0.98) |
| Span / area / aspect ratio | 1.32 m / 0.247 m² / 7.0 |
| Root / tip chord | 44.1 / 12.9 cm (tip Re 150,000) |
| Spar tube, root / tip | r 5.6 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.2 m/s, 0.47, 11.6 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 72 W / 117 min |
| Mission time estimate (+20% reserve) | 97 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.11 | 0.88 | 114 / 117 | 90% | 87 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.3 min after launch |
| Pod reached | 90% (goal 90%); goal at 94.3 min |
| Time on task | 87.0 min |
| Search plan | 49 m track spacing, effective sweep width 148 m, 2 pattern pass(es) |
| Flight time / distance | 95.4 min / 73.2 km |
| Battery left at recovery | 19% |
| Mean power, max bank | 72 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

