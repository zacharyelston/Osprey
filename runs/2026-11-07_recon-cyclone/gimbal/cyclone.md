# Recon as a Cyclone: gimbal

Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter: twisted one way the tip motors push up and it flies as a tricopter; twisted the other they push round and the whole bird spins, its arms the blades. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in `design/recon/cyclone.toml`.

## The bird

| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs |
|---|---|---|---|
| Mass | 2.73 kg | 2.78 kg | **3.12 kg** |
| Wing | 0.278 m², 2.02 m span | the same, in three arms | 0.279 m² (chord ×1.00); rotor 2.18 m across |
| Battery | 1.27 kg | the same | 1.58 kg |
| Search speed | 16.2 m/s | the same | 19.5 m/s |
| Jobs done, as a stopped wing | 7 / 7 | 6 / 7 | 7 / 7 |
| Jobs done, as a tricopter | | 3 / 7 | |

Against the tailsitter one-bird for the same cameras: 2.96 kg, 1.81 m span.

## Spinning

| | Cyclone | Tailsitter |
|---|---|---|
| Hover power | **174 W** at 215 rpm, tips at 24.6 m/s: induced 64, arms' drag 18, nacelles 22 W, through the tip props | 410 W on two 30 cm props |
| Figure of merit (ideal power over what it takes) | 0.32 | |
| Hover energy per sortie | 4.1 Wh: 29 s spinning and 2 × 8 s as a tricopter (469 W) to and from the wing | 6.0 Wh |
| Motors | three, 696 W peak in all, 0.21 kg: sized by the tricopter transition at 1.3 × weight | 828 W, 0.22 kg |
| Spin-up from rest to lift-off | 0.3 s, plus the motors' spool | 4.3 s to wing-borne |
| Hover on one motor | ✓ 232 W against 174 W needed | ✗ |
| Wind it can hover in | 8.6 m/s, before the retreating arm stalls (advance ratio 0.35) | 11.9 m/s |
| The camera, spinning | turns 87 px in a 1 ms exposure: blind unless de-spun | steady |

## Motors off: down like a seed

- Sinks at **3.3 m/s** on the spinning disc (drag coefficient 1.2 on 3.75 m²): parachute speed, with nothing to deploy.
- The spin holds 110 J against the sink's 17 J (6.4×): pitching the arms up just before the water can stop the sink.
- Into the water at the sink speed: 6.7 g; flared: 1.0 g. The structure is sized for 3 g.

## Cruising

- **Stopped as a wing:** one arm aft as the tail, two forward at ±60°, 14.2 m/s stall on symmetric sections (CL max 0.9). One forward arm flies backwards in the spin, so it flips over to cruise. Recovery is a vertical spin, so the 12 m/s stall limit for a catch doesn't apply.
- **As a tricopter:** no wing lift; it takes 484 W at best, against 84 W for the twin-boom.

| Job | As built, stopped wing | As built, tricopter | Re-sized, stopped wing |
|---|---|---|---|
| escort-flanks | ✓ 50% left | ✗ 1% left, 430 W | ✓ 39% left |
| inspect-vessel | ✓ 87% left | ✓ 60% left, 503 W | ✓ 88% left |
| sar-convoy | ✓ 54% left | ✗ 6% left, 511 W | ✓ 61% left |
| sar-datum | ✓ 75% left | ✓ 14% left, 452 W | ✓ 81% left |
| sar-offshore | ✗ 0% left | ✗ 4% left, 501 W | ✓ 1% left |
| scout-anchorage | ✓ 76% left | ✓ 20% left, 473 W | ✓ 77% left |
| scout-island | ✓ 69% left | ✗ 1% left, 441 W | ✓ 68% left |

Not modelled: floating and launching from the water (it would float flat, so the tip props need pylons), the transition between the spin and the wing (here a fixed time as a tricopter), stability and control in each mode, a de-spun camera mount, and the arms' structure under the spin's loads.
