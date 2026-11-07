# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.79 kg (battery 0.16, shell 0.15, spar 0.023, fixed 1.46) |
| Span / area / aspect ratio | 1.25 m / 0.173 m² / 9.0 |
| Root / tip chord | 14.4 / 13.3 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.6 m/s, 0.60, 6.3 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 105 W / 14 min |
| Mission time estimate (+20% reserve) | 12 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.89 | 0.24 | 21 / 33 | 100% | 4 |
| 2 | 0.64 | 1.79 | 0.16 | 21 / 33 | 100% | 4 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.2 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 6.8 min |
| Time on task | 3.6 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (inboard PTZ eye); 37 px across; resolves it |
| Flight time / distance | 13.4 min / 9.8 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 93 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

