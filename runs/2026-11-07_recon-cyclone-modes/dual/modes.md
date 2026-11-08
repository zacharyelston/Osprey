# The Cyclone's modes: dual

A: the motors at the arm tips. A2: optional motors half-way along each arm. B: the blade servos that twist each arm about its own axis, and its motors with it. Sized with **A alone**; the other is compared below. REF inputs in `[modes]` of `design/recon/cyclone.toml`.

## The modes

| Mode | B | A (A2) | What it can do |
|---|---|---|---|
| 1 lift-off and landing | centred: the chords and A point up | lifting | a tricopter: 300 W to hover, 1.5 m/s up the first 7.6 m (25 ft), 1 m/s down the last; peak 445 W at the burst |
| 2 spinning hover | pitched off centre, left or right: which way it spins | pushing round; PWM, varied once a turn, steers | a spinning prop: 123 W to hover, 2 m/s climbs |
| 3 spinning travel | as 2 | as 2, the disc tilted 10° | best range 7 m/s at 85 W; top 7 m/s (the retreating arm); 22 km on the battery |
| 4 wing-borne travel | forward: two arms up, the 30° dihedral wing; one down, the fin | pushing forward; PWM fine, B large | flies from 14 m/s; the jobs, in `cyclone.md` |

## The moves

Each move from where a standard sortie makes it. A guard is what has to be true first.

| Move | From | Guard | Time | Height | Energy | What happens |
|---|---|---|---|---|---|---|
| 1 → 2 | 8 m, 0 m/s | at 7.6 m or above | 3.0 s | +0 m | 0.29 Wh | B off centre, the spin builds |
| 2 → 1 | 17 m, 0 m/s | at 7.6 m or above | 3.0 s | +0 m | 0.29 Wh | B to centre, A takes the weight |
| 2 → 3 | 17 m, 0 m/s | spinning | 3.9 s | +0 m | 0.12 Wh | disc tilted, speeding up |
| 3 → 2 | 17 m, 7 m/s | spinning | 3.9 s | +0 m | 0.12 Wh | disc levelled, slowing |
| 3 → 4 | 17 m, 7 m/s | from 17 m: the pitch-over's loss over the 10 m margin | 8.2 s | -7 m | 0.98 Wh | B to centre as the spin dies, pitch over to wing-borne |
| 4 → 1 | 10 m, 14 m/s | A holds the weight at the top, and the stint on A under 20 s | 5.9 s | -0 m | 0.48 Wh | pitch up until A points up |
| 4 → 3 | 17 m, 14 m/s | from 10 m | 3.5 s | +1 m | 0.00 Wh | forced pull-up, the inflow spins it up |

Any other move goes along these: 1 to 4 is 1 → 2 → 3 → 4; 4 to 2 is 4 → 3 → 2.

## Sorties

**Launch, from the deck or the water to wing-borne:** 25 s, 2.20 Wh, 8 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 1 | mode 1 climb | 5.1 s | 0 → 8 m | 0.53 Wh |
| 1 | B off centre, the spin builds | 3.0 s | 8 → 8 m | 0.29 Wh |
| 2 | mode 2 climb | 4.8 s | 8 → 17 m | 0.28 Wh |
| 2 | disc tilted, speeding up | 3.9 s | 17 → 17 m | 0.12 Wh |
| 3 | B to centre as the spin dies, pitch over to wing-borne | 8.2 s | 17 → 10 m | 0.98 Wh |

**Recovery, from wing-borne back aboard:** 19 s, 1.26 Wh, 11 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | forced pull-up, the inflow spins it up | 3.5 s | 17 → 18 m | 0.00 Wh |
| 3 | disc levelled, slowing | 0.0 s | 18 → 18 m | 0.00 Wh |
| 2 | mode 2 descent | 5.4 s | 18 → 8 m | 0.22 Wh |
| 2 | B to centre, A takes the weight | 3.0 s | 8 → 8 m | 0.29 Wh |
| 1 | mode 1 descent | 7.6 s | 8 → 0 m | 0.75 Wh |

**Recovery straight from 4 to 1, tried (from 10 m, as low as the pitch-up allows):** 16 s, 1.47 Wh, 16 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | pitch up until A points up | 5.9 s | 10 → 10 m | 0.48 Wh |
| 1 | mode 1 descent | 10.0 s | 10 → 0 m | 0.98 Wh |

The pitch-up from 14 m/s takes 5.9 s and 42 m, loses 0.1 m, and ends hovering on A at 0.77 × its burst. It works; it just keeps A at its burst, low, for the whole stint.

## A alone, or A with A2

| | A alone | A and A2 |
|---|---|---|
| Mass | 2.32 kg | 2.38 kg |
| Motors | 0.13 kg: A 297 W | 0.19 kg: A 261 W, A2 109 W |
| Mode 1 hover | 300 W | 222 W |
| Pitch-over (3 → 4): height lost | 7 m | 0 m |
| Launch + recovery | 3.5 Wh | 2.2 Wh |
| One motor out in mode 1 | falls | holds 1.54 × the weight |

Mode 1 is the exposure: 19 s a sortie at or under 7.6 m with A alone carrying the weight. Three motors can't lose one, and a fall from 7.6 m takes 1.2 s, less than B's 3 s turn into the spin: it hits at 12 m/s. With A2, five of six props are left to hold it.

## A motor out, mode by mode

- **2 and 3, spinning:** at the burst, one motor holds the spinning hover; with none, it comes down like a seed at 3.7 m/s, and the spin holds 3.5× the sink's energy to flare with.
- **4, wing-borne:** a glider; the forced pull-up (4 → 3) leads to the same seed fall.
- **1, under 7.6 m:** see above.

Not modelled: the spin dying and building as dynamics (fixed times), stability and control in each mode, the authority of A's PWM and of B, wind in modes 1 and 2, and the deck's motion.
