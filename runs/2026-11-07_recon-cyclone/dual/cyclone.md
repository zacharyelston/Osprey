# Recon as a Cyclone: dual

Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter: twisted one way the tip motors push up and it flies as a tricopter; twisted the other they push round and the whole bird spins, its arms the blades. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in `design/recon/cyclone.toml`.

## The bird

| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs |
|---|---|---|---|
| Mass | 2.13 kg | 2.10 kg | **2.34 kg** |
| Wing | 0.206 m², 1.54 m span | the same, in three arms | 0.287 m² (chord ×1.39); rotor 1.70 m across |
| Battery | 0.59 kg | the same | 0.71 kg |
| Search speed | 16.7 m/s | the same | 16.7 m/s |
| Jobs done, as a stopped wing | 7 / 7 | 6 / 7 | 7 / 7 |
| Jobs done, as a tricopter | | 2 / 7 | |

Against the tailsitter one-bird for the same cameras: 2.22 kg, 1.40 m span.

## Spinning

| | Cyclone | Tailsitter |
|---|---|---|
| Hover power | **131 W** at 233 rpm, tips at 20.8 m/s: induced 54, arms' drag 12, nacelles 13 W, through the tip props | 265 W on two 30 cm props |
| Figure of merit (ideal power over what it takes) | 0.36 | |
| Hover energy per sortie | 2.8 Wh: 29 s spinning and 2 × 8 s as a tricopter (306 W) to and from the wing | 3.9 Wh |
| Motors | three, 454 W peak in all, 0.16 kg: sized by the tricopter transition at 1.3 × weight | 537 W, 0.16 kg |
| Spin-up from rest to lift-off | 0.3 s, plus the motors' spool | 4.3 s to wing-borne |
| Hover on one motor | ✓ 151 W against 131 W needed | ✗ |
| Wind it can hover in | 7.3 m/s, before the retreating arm stalls (advance ratio 0.35) | 11.9 m/s |
| The camera, spinning | turns 94 px in a 1 ms exposure: blind unless de-spun | steady |

## Motors off: down like a seed

- Sinks at **3.7 m/s** on the spinning disc (drag coefficient 1.2 on 2.28 m²): parachute speed, with nothing to deploy.
- The spin holds 67 J against the sink's 16 J (4.2×): pitching the arms up just before the water can stop the sink.
- Into the water at the sink speed: 8.0 g; flared: 1.0 g. The structure is sized for 3 g.

## Cruising

- **Stopped as a wing:** one arm aft as the tail, two forward at ±60°, 12.1 m/s stall on symmetric sections (CL max 0.9). One forward arm flies backwards in the spin, so it flips over to cruise. Recovery is a vertical spin, so the 12 m/s stall limit for a catch doesn't apply.
- **As a tricopter:** no wing lift; it takes 325 W at best, against 71 W for the twin-boom.

| Job | As built, stopped wing | As built, tricopter | Re-sized, stopped wing |
|---|---|---|---|
| escort-flanks | ✗ 2% left | ✗ 1% left, 319 W | ✓ 2% left |
| inspect-vessel | ✓ 73% left | ✓ 34% left, 360 W | ✓ 75% left |
| sar-convoy | ✓ 50% left | ✗ 8% left, 385 W | ✓ 49% left |
| sar-datum | ✓ 85% left | ✓ 61% left, 343 W | ✓ 87% left |
| sar-offshore | ✓ 35% left | ✗ 0% left, 388 W | ✓ 41% left |
| scout-anchorage | ✓ 59% left | ✗ 9% left, 355 W | ✓ 63% left |
| scout-island | ✓ 62% left | ✗ 1% left, 325 W | ✓ 64% left |

Not modelled: floating and launching from the water (it would float flat, so the tip props need pylons), the transition between the spin and the wing (here a fixed time as a tricopter), stability and control in each mode, a de-spun camera mount, and the arms' structure under the spin's loads.
