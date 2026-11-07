# Recon as a Cyclone: gimbal

Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter. It hovers only by spinning, the whole bird a rotor and its arms the blades. It flies with the arms twisted 90°, two up at 30° dihedral as the wing and one down as the fin, all three tip motors pushing forward. The motors push up only for the few seconds it takes to pull clear of the water on a sea launch. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in `design/recon/cyclone.toml`.

## The bird

| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs | Tailsitter one-bird |
|---|---|---|---|---|
| Mass | 2.73 kg | 2.73 kg | **2.91 kg** | 2.96 kg |
| Size | 2.02 m span | 2.18 m rotor | 2.18 m rotor, 1.89 m flying span, chord ×1.08 | 1.81 m span |
| Battery | 1.27 kg | the same | 1.41 kg | |
| Motors | one pusher | three at the tips, rated 381 W | three, rated 419 W, 0.15 kg | 828 W, 0.22 kg |
| Search speed, over the stall banked 35° | 16.2 m/s | the same, only 1.03× | 19.5 m/s, 1.25× (the limit is 1.25×) | |
| Jobs done | 7 / 7 | 7 / 7 | 7 / 7 | 7 / 7 |

The motors are rated for the larger of the spinning peak (309 W at 1.6 × weight) and the sea lift-off (628 W at 1.3 × weight) carried at 1.5 × the rating for its few seconds.

## What each mode can do

| Mode | Ability | |
|---|---|---|
| Spinning | Hover | **153 W** shaft at 200 rpm, tips at 22.9 m/s (tailsitter 410 W); figure of merit 0.33 |
| | Hover on the whole battery | 70 min at 194 W from the battery |
| | Climb | 6.2 m/s on the rated power, 10.1 m/s at the burst |
| | Wind it can hold station in | 8.0 m/s, before the retreating arm stalls (tailsitter 11.9 m/s) |
| | Spin-up from rest | 0.4 s, plus the motors' spool |
| | One motor | ✗ rated 140 W, ✓ at the burst 209 W, against 153 W to hover |
| | The camera | turns 81 px in a 1 ms exposure: blind unless de-spun |
| Motors off | Seed fall | **3.2 m/s**; the spin holds 5.5× the sink's energy, so a flare can stop it (6.3 g into the water unflared) |
| Flight | Stall | 14.1 m/s (twin-boom 11.7) |
| | Least power | 126 W at 16.9 m/s (twin-boom 72 W) |
| | Best lift-to-drag | 8.2 (twin-boom 12.2) |
| | Top speed | 29 m/s on the rated power, 33 m/s at the burst (twin-boom 30) |
| | Endurance, range on the battery | 1.8 h, 108 km (twin-boom 2.8 h, 142 km) |
| | Control | the tip motors' PWM for the fine corrections, the arms' twist servos for the large |
| Sea lift-off | As a tricopter | 1.30 × weight at the burst, for 3 s, then it twists into the spin |

## The transitions

- **Spin to wing:** climb spinning to **21 m** (10 s at 2 m/s), drive the arms to the flight setting as the spin dies, pitch over nose-down (60°) and fly out: 11 m lost, 1.8 s, 23 m on, 22.6 m/s at the bottom, 10 m above the water.
- **Wing to spin:** pitch up hard from 17 m/s: the zoom gains 12 m, the inflow spins the rotor up in about 2 s for 6 m, +5 m in all. Powered from there, or an autogyro.
- **Each sortie off the wing**, as the tailsitter's 45 s: 42 s spinning, 3 s lifting off the sea and the climb to the fly-out: **3.0 Wh** (tailsitter 6.0 Wh).

## The jobs

| Job | As built | Re-sized |
|---|---|---|
| escort-flanks | ✓ 57% left, 110 W | ✓ 39% left |
| inspect-vessel | ✓ 88% left, 121 W | ✓ 88% left |
| sar-convoy | ✓ 60% left, 118 W | ✓ 61% left |
| sar-datum | ✓ 78% left, 113 W | ✓ 82% left |
| sar-offshore | ✓ 3% left, 110 W | ✓ 1% left |
| scout-anchorage | ✓ 78% left, 118 W | ✓ 77% left |
| scout-island | ✓ 73% left, 112 W | ✓ 69% left |

Not modelled: floating and the sea lift-off itself (it floats flat, so the tip props need pylons), the spin dying and starting again (the fly-out starts with it stopped; the entry is a fixed time), stability and control in each mode, the PWM and servo authority, a de-spun camera mount, and the arms' loads in the spin.
