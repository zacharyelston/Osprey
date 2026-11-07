# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-06 at unknown by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.31 kg (battery 0.15, shell 0.16, spar 0.019, fixed 0.98) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 13.1 cm (tip Re 266,415) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 30.0 m/s, 0.13, 3.4 |
| Stall speed (sea level) | 11.0 m/s (limit 12) |
| Task power / endurance | 229 W / 6 min |
| Mission time estimate (+20% reserve) | 4 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.31 | 0.15 | 12 / 20 | 100% | 3 |
| 2 | 0.61 | 1.31 | 0.15 | 14 / 29 | 100% | 2 |
| 3 | 0.50 | 1.31 | 0.15 | 15 / 31 | 100% | 2 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.4 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 5.1 min |
| Time on task | 1.7 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (gimbal); 37 px across; resolves it |
| Flight time / distance | 10.7 min / 10.0 km |
| Battery left at recovery | 37% |
| Mean power, max bank | 85 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

