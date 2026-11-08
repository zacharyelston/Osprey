# Recon as a Cyclone: gimbal

Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter. It hovers only by spinning, the whole bird a rotor and its arms the blades. It flies with the arms twisted 90°, two up at 30° dihedral as the wing and one down as the fin, all three tip motors pushing forward. The motors push up only for the few seconds it takes to pull clear of the water on a sea launch. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in `design/recon/cyclone.toml`.

## The bird

| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs | Tailsitter one-bird |
|---|---|---|---|---|
| Mass | 2.73 kg | 2.73 kg | **2.95 kg** | 2.96 kg |
| Size | 2.02 m span | 2.18 m rotor | 2.18 m rotor, 1.89 m flying span, chord ×1.00 | 1.81 m span |
| Battery | 1.27 kg | the same | 1.47 kg | |
| Motors | one pusher | three at the tips, rated 381 W | three, rated 426 W, 0.15 kg | 828 W, 0.22 kg |
| Search speed, over the stall banked 35° | 16.2 m/s | the same, only 1.03× | 21.1 m/s, 1.29× (the limit is 1.25×) | |
| Jobs done | 7 / 7 | 7 / 7 | 7 / 7 | 7 / 7 |

A: A is rated for the larger of the spinning peak (324 W at 1.6 × weight) and its share of mode 1's (640 W at 1.3 × weight), which it carries at 1.5 × the rating for a stint of 11 s at most. The modes, the moves between them and A2 are in `modes.md`.

## What each mode can do

| Mode | Ability | |
|---|---|---|
| Spinning | Hover | **160 W** shaft at 209 rpm, tips at 23.9 m/s (tailsitter 410 W); figure of merit 0.32 |
| | Hover on the whole battery | 70 min at 202 W from the battery |
| | Climb | 6.1 m/s on the rated power, 10.1 m/s at the burst |
| | Wind it can hold station in | 8.4 m/s, before the retreating arm stalls (tailsitter 11.9 m/s) |
| | The spin building (1->2) | 0.5 s on A's rating, inside B's 3 s turn |
| Spinning travel (3) | Best range | 8 m/s at 122 W, up to 8 m/s (the retreating arm); 1.5 h, 44 km on the battery |
| | One motor | ✗ rated 142 W, ✓ at the burst 213 W, against 160 W to hover |
| | The camera | turns 85 px in a 1 ms exposure: blind unless de-spun |
| Motors off | Seed fall | **3.2 m/s**; the spin holds 5.7× the sink's energy, so a flare can stop it (6.3 g into the water unflared) |
| Flight | Stall | 14.8 m/s (twin-boom 11.7) |
| | Least power | 135 W at 17.7 m/s (twin-boom 72 W) |
| | Best lift-to-drag | 8.0 (twin-boom 12.2) |
| | Top speed | 29 m/s on the rated power, 33 m/s at the burst (twin-boom 30) |
| | Endurance, range on the battery | 1.7 h, 108 km (twin-boom 2.8 h, 142 km) |
| | Control | A's PWM for the fine corrections, B for the large |
| Lift-off and landing (1) | B centred, A lifting | 432 W to hover, the first 7.6 m up and the last down |

## Launch and recovery

Run by the modes' manager (`modes.md`): up in 1 to 7.6 m, 2, up to 26 m, 3, pitch over to 4; back by the forced pull-up, 3, 2, down to the clearance, 1, down. Launch 32 s, recovery 27 s: **6.0 Wh** a sortie off the wing (tailsitter 6.0 Wh).

## The jobs

| Job | As built | Re-sized |
|---|---|---|
| escort-flanks | ✓ 56% left, 110 W | ✓ 30% left |
| inspect-vessel | ✓ 88% left, 121 W | ✓ 88% left |
| sar-convoy | ✓ 59% left, 118 W | ✓ 64% left |
| sar-datum | ✓ 78% left, 113 W | ✓ 82% left |
| sar-offshore | ✓ 1% left, 110 W | ✓ 1% left |
| scout-anchorage | ✓ 78% left, 118 W | ✓ 73% left |
| scout-island | ✓ 72% left, 112 W | ✓ 60% left |

Not modelled: floating and lifting off the water (B centred points A's props up, clear of it), the spin dying and building as dynamics (each is a fixed time), stability and control in each mode, the PWM and servo authority, a de-spun camera mount, and the arms' loads in the spin.
