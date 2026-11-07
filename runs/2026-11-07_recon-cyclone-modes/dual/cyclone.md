# Recon as a Cyclone: dual

Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter. It hovers only by spinning, the whole bird a rotor and its arms the blades. It flies with the arms twisted 90°, two up at 30° dihedral as the wing and one down as the fin, all three tip motors pushing forward. The motors push up only for the few seconds it takes to pull clear of the water on a sea launch. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in `design/recon/cyclone.toml`.

## The bird

| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs | Tailsitter one-bird |
|---|---|---|---|---|
| Mass | 2.13 kg | 2.07 kg | **2.30 kg** | 2.22 kg |
| Size | 1.54 m span | 1.70 m rotor | 1.70 m rotor, 1.47 m flying span, chord ×1.57 | 1.40 m span |
| Battery | 0.59 kg | the same | 0.65 kg | |
| Motors | one pusher | three at the tips, rated 251 W | three, rated 293 W, 0.12 kg | 537 W, 0.16 kg |
| Search speed, over the stall banked 35° | 16.7 m/s | the same, only 1.05× | 16.7 m/s, 1.25× (the limit is 1.25×) | |
| Jobs done | 7 / 7 | 7 / 7 | 7 / 7 | 7 / 7 |

The motors are rated for the larger of the spinning peak (247 W at 1.6 × weight) and the sea lift-off (439 W at 1.3 × weight) carried at 1.5 × the rating for its few seconds.

## What each mode can do

| Mode | Ability | |
|---|---|---|
| Spinning | Hover | **122 W** shaft at 217 rpm, tips at 19.3 m/s (tailsitter 265 W); figure of merit 0.37 |
| | Hover on the whole battery | 39 min at 162 W from the battery |
| | Climb | 5.3 m/s on the rated power, 8.9 m/s at the burst |
| | Wind it can hold station in | 6.8 m/s, before the retreating arm stalls (tailsitter 11.9 m/s) |
| | Spin-up from rest | 0.4 s, plus the motors' spool |
| | One motor | ✗ rated 98 W, ✓ at the burst 146 W, against 122 W to hover |
| | The camera | turns 88 px in a 1 ms exposure: blind unless de-spun |
| Motors off | Seed fall | **3.7 m/s**; the spin holds 3.6× the sink's energy, so a flare can stop it (7.9 g into the water unflared) |
| Flight | Stall | 12.1 m/s (twin-boom 12.0) |
| | Least power | 97 W at 14.5 m/s (twin-boom 76 W) |
| | Best lift-to-drag | 7.8 (twin-boom 9.8) |
| | Top speed | 25 m/s on the rated power, 29 m/s at the burst (twin-boom 31) |
| | Endurance, range on the battery | 1.0 h, 54 km (twin-boom 1.2 h, 64 km) |
| | Control | the tip motors' PWM for the fine corrections, the arms' twist servos for the large |
| Sea lift-off | As a tricopter | 1.30 × weight at the burst, for 3 s, then it twists into the spin |

## The transitions

- **Spin to wing:** climb spinning to **20 m** (10 s at 2 m/s), drive the arms to the flight setting as the spin dies, pitch over nose-down (60°) and fly out: 10 m lost, 1.8 s, 21 m on, 20.8 m/s at the bottom, 10 m above the water.
- **Wing to spin:** pitch up hard from 14 m/s: the zoom gains 9 m, the inflow spins the rotor up in about 2 s for 7 m, +1 m in all. Powered from there, or an autogyro.
- **Each sortie off the wing**, as the tailsitter's 45 s: 42 s spinning, 3 s lifting off the sea and the climb to the fly-out: **2.4 Wh** (tailsitter 3.9 Wh).

## The jobs

| Job | As built | Re-sized |
|---|---|---|
| escort-flanks | ✓ 9% left, 107 W | ✓ 1% left |
| inspect-vessel | ✓ 76% left, 114 W | ✓ 75% left |
| sar-convoy | ✓ 57% left, 115 W | ✓ 49% left |
| sar-datum | ✓ 86% left, 119 W | ✓ 87% left |
| sar-offshore | ✓ 42% left, 112 W | ✓ 41% left |
| scout-anchorage | ✓ 62% left, 114 W | ✓ 63% left |
| scout-island | ✓ 66% left, 110 W | ✓ 64% left |

Not modelled: floating and the sea lift-off itself (it floats flat, so the tip props need pylons), the spin dying and starting again (the fly-out starts with it stopped; the entry is a fixed time), stability and control in each mode, the PWM and servo authority, a de-spun camera mount, and the arms' loads in the spin.
