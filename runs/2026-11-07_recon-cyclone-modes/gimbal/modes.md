# The Cyclone's modes: gimbal

A: the motors at the arm tips. A2: optional motors half-way along each arm. B: the blade servos that twist each arm about its own axis, and its motors with it. Sized with **A alone**; the other is compared below. REF inputs in `[modes]` of `design/recon/cyclone.toml`.

## The modes

| Mode | B | A (A2) | What it can do |
|---|---|---|---|
| 1 lift-off and landing | centred: the chords and A point up | lifting | a tricopter: 432 W to hover, 1.5 m/s up the first 7.6 m (25 ft), 1 m/s down the last; peak 640 W at the burst |
| 2 spinning hover | pitched off centre, left or right: which way it spins | pushing round; PWM, varied once a turn, steers | a spinning prop: 160 W to hover, 2 m/s climbs |
| 3 spinning travel | as 2 | as 2, the disc tilted 10° | best range 8 m/s at 122 W; top 8 m/s (the retreating arm); 44 km on the battery |
| 4 wing-borne travel | forward: two arms up, the 30° dihedral wing; one down, the fin | pushing forward; PWM fine, B large | flies from 18 m/s; the jobs, in `cyclone.md` |

## The moves

Each move from where a standard sortie makes it. A guard is what has to be true first.

| Move | From | Guard | Time | Height | Energy | What happens |
|---|---|---|---|---|---|---|
| 1 → 2 | 8 m, 0 m/s | at 7.6 m or above | 3.0 s | +0 m | 0.42 Wh | B off centre, the spin builds |
| 2 → 1 | 26 m, 0 m/s | at 7.6 m or above | 3.0 s | +0 m | 0.42 Wh | B to centre, A takes the weight |
| 2 → 3 | 26 m, 0 m/s | spinning | 4.8 s | +0 m | 0.18 Wh | disc tilted, speeding up |
| 3 → 2 | 26 m, 8 m/s | spinning | 4.8 s | +0 m | 0.18 Wh | disc levelled, slowing |
| 3 → 4 | 26 m, 8 m/s | from 26 m: the pitch-over's loss over the 10 m margin | 10.4 s | -16 m | 1.87 Wh | B to centre as the spin dies, pitch over to wing-borne |
| 4 → 1 | 10 m, 18 m/s | A holds the weight at the top, and the stint on A under 20 s | 7.9 s | -0 m | 0.99 Wh | pitch up until A points up |
| 4 → 3 | 26 m, 18 m/s | from 10 m | 3.8 s | +6 m | 0.00 Wh | forced pull-up, the inflow spins it up |

Any other move goes along these: 1 to 4 is 1 → 2 → 3 → 4; 4 to 2 is 4 → 3 → 2.

## Sorties

**Launch, from the deck or the water to wing-borne:** 32 s, 3.91 Wh, 8 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 1 | mode 1 climb | 5.1 s | 0 → 8 m | 0.76 Wh |
| 1 | B off centre, the spin builds | 3.0 s | 8 → 8 m | 0.42 Wh |
| 2 | mode 2 climb | 9.1 s | 8 → 26 m | 0.68 Wh |
| 2 | disc tilted, speeding up | 4.8 s | 26 → 26 m | 0.18 Wh |
| 3 | B to centre as the spin dies, pitch over to wing-borne | 10.4 s | 26 → 10 m | 1.87 Wh |

**Recovery, from wing-borne back aboard:** 27 s, 2.14 Wh, 11 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | forced pull-up, the inflow spins it up | 3.8 s | 26 → 32 m | 0.00 Wh |
| 3 | disc levelled, slowing | 0.0 s | 32 → 32 m | 0.00 Wh |
| 2 | mode 2 descent | 12.3 s | 32 → 8 m | 0.64 Wh |
| 2 | B to centre, A takes the weight | 3.0 s | 8 → 8 m | 0.42 Wh |
| 1 | mode 1 descent | 7.6 s | 8 → 0 m | 1.07 Wh |

**Recovery straight from 4 to 1, tried (from 10 m, as low as the pitch-up allows):** 18 s, 2.40 Wh, 18 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | pitch up until A points up | 7.9 s | 10 → 10 m | 0.99 Wh |
| 1 | mode 1 descent | 10.0 s | 10 → 0 m | 1.41 Wh |

The pitch-up from 18 m/s takes 7.9 s and 59 m, loses 0.3 m, and ends hovering on A at 0.77 × its burst. It works; it just keeps A at its burst, low, for the whole stint.

## A alone, or A with A2

| | A alone | A and A2 |
|---|---|---|
| Mass | 2.95 kg | 3.01 kg |
| Motors | 0.15 kg: A 426 W | 0.22 kg: A 335 W, A2 156 W |
| Mode 1 hover | 432 W | 315 W |
| Pitch-over (3 → 4): height lost | 16 m | 10 m |
| Launch + recovery | 6.0 Wh | 4.7 Wh |
| One motor out in mode 1 | falls | holds 1.47 × the weight |

Mode 1 is the exposure: 19 s a sortie at or under 7.6 m with A alone carrying the weight. Three motors can't lose one, and a fall from 7.6 m takes 1.2 s, less than B's 3 s turn into the spin: it hits at 12 m/s. With A2, five of six props are left to hold it.

## A motor out, mode by mode

- **2 and 3, spinning:** at the burst, one motor holds the spinning hover; with none, it comes down like a seed at 3.2 m/s, and the spin holds 5.7× the sink's energy to flare with.
- **4, wing-borne:** a glider; the forced pull-up (4 → 3) leads to the same seed fall.
- **1, under 7.6 m:** see above.

Not modelled: the spin dying and building as dynamics (fixed times), stability and control in each mode, the authority of A's PWM and of B, wind in modes 1 and 2, and the deck's motion.
