# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-06 at unknown by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.37 kg (battery 0.15, shell 0.14, spar 0.027, fixed 1.05) |
| Span / area / aspect ratio | 1.40 m / 0.164 m² / 12.0 |
| Root / tip chord | 13.3 / 13.3 cm (tip Re 270,648) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 30.0 m/s, 0.15, 3.1 |
| Stall speed (sea level) | 11.6 m/s (limit 12) |
| Task power / endurance | 261 W / 6 min |
| Mission time estimate (+20% reserve) | 4 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.37 | 0.15 | 13 / 20 | 100% | 3 |
| 2 | 0.63 | 1.37 | 0.15 | 16 / 32 | 100% | 2 |
| 3 | 0.50 | 1.37 | 0.15 | 17 / 36 | 100% | 2 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.3 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 5.0 min |
| Time on task | 1.7 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (gimbal); 37 px across; resolves it |
| Flight time / distance | 11.3 min / 10.1 km |
| Battery left at recovery | 30% |
| Mean power, max bank | 89 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

