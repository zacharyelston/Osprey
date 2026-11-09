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

A: A is rated for the larger of the spinning peak (247 W at 1.6 × weight) and its share of mode 1's (439 W at 1.3 × weight), which it carries at 1.5 × the rating for a stint of 11 s at most. The modes, the moves between them and A2 are in `modes.md`.

## What each mode can do

| Mode | Ability | |
|---|---|---|
| Spinning | Hover | **122 W** shaft at 217 rpm, tips at 19.3 m/s (tailsitter 265 W); figure of merit 0.37 |
| | Hover on the whole battery | 39 min at 162 W from the battery |
| | Climb | 5.3 m/s on the rated power, 8.9 m/s at the burst |
| | Wind it can hold station in | 3.5 m/s spinning, until the retreating arm stalls; 10.2 m/s in mode 1 (tailsitter 11.9 m/s) |
| | The spin building (1->2), dying (2->1) | 1.4 s, 1.6 s (`dynamics.md`) |
| Spinning travel (3) | Best range | 4 m/s at 89 W, up to 4 m/s (the retreating arm stalls); 0.8 h, 11 km on the battery |
| | One motor | ✗ rated 98 W, ✓ at the burst 146 W, against 122 W to hover |
| | The camera | turns 88 px in a 1 ms exposure: blind unless de-spun |
| Motors off | Seed fall | **3.7 m/s**; the spin holds 3.6× the sink's energy, so a flare can stop it (7.9 g into the water unflared) |
| Flight | Stall | 12.1 m/s (twin-boom 12.0) |
| | Least power | 97 W at 14.5 m/s (twin-boom 76 W) |
| | Best lift-to-drag | 7.8 (twin-boom 9.8) |
| | Top speed | 25 m/s on the rated power, 29 m/s at the burst (twin-boom 31) |
| | Endurance, range on the battery | 1.0 h, 54 km (twin-boom 1.2 h, 64 km) |
| | Control | A's PWM for the fine corrections, B for the large |
| Lift-off and landing (1) | B centred, A lifting | 296 W to hover, the first 7.6 m up and the last down |

## Launch and recovery

Run by the modes' manager (`modes.md`): up in 1 to 7.6 m, 2, up to 10 m, 3, pitch over to 4; back by the forced pull-up, 3, 2, down to the clearance, 1, down. Launch 14 s, recovery 14 s: **2.3 Wh** a sortie off the wing (tailsitter 3.9 Wh).

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

The spin building and dying, A's and B's authority and the wind are in `dynamics.md`; floating and the launch from the water in `water.md`. Not modelled: closed-loop stability in each mode, a de-spun camera mount, and the arms' loads in the spin.
