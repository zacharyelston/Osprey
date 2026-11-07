# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.65 kg (battery 0.15, shell 0.14, spar 0.022, fixed 1.34) |
| Span / area / aspect ratio | 1.20 m / 0.159 m² / 9.0 |
| Root / tip chord | 13.7 / 12.9 cm (tip Re 169,550) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 19.5 m/s, 0.44, 5.1 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 134 W / 11 min |
| Mission time estimate (+20% reserve) | 9 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.73 | 0.22 | 19 / 30 | 100% | 4 |
| 2 | 0.64 | 1.65 | 0.15 | 19 / 31 | 100% | 3 |
| 3 | 0.62 | 1.65 | 0.15 | 19 / 32 | 100% | 3 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.2 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 5.8 min |
| Time on task | 2.6 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (inboard PTZ eye); 37 px across; resolves it |
| Flight time / distance | 12.4 min / 9.7 km |
| Battery left at recovery | 19% |
| Mean power, max bank | 94 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

