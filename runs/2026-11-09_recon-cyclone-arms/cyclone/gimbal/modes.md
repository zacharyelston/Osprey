# The Cyclone's modes: gimbal

A: the motors at the arm tips. A2: optional motors half-way along each arm. B: the blade servos that twist each arm about its own axis, and its motors with it. Sized with **A alone**; the other is compared below. REF inputs in `[modes]` of `design/recon/cyclone.toml`.

## The modes

| Mode | B | A (A2) | What it can do |
|---|---|---|---|
| 1 lift-off and landing | centred: the chords and A point up | lifting | a tricopter: 428 W to hover, 1.5 m/s up the first 7.6 m (25 ft), 1 m/s down the last; peak 634 W at the burst |
| 2 spinning hover | pitched off centre, left or right: which way it spins | pushing round; PWM, varied once a turn, steers | a spinning prop: 159 W to hover, 2 m/s climbs |
| 3 spinning travel | as 2 | as 2, the disc tilted 10° | best range 4 m/s at 111 W; top 4 m/s (the retreating arm stalls); 25 km on the battery |
| 4 wing-borne travel | forward: two arms up, the 30° dihedral wing; one down, the fin | pushing forward; PWM fine, B large | flies from 18 m/s; the jobs, in `cyclone.md` |

## The moves

Each move from where a standard sortie makes it. A guard is what has to be true first.

| Move | From | Guard | Time | Height | Energy | What happens |
|---|---|---|---|---|---|---|
| 1 → 2 | 8 m, 0 m/s | at 7.6 m or above | 1.3 s | +0 m | 0.20 Wh | B off centre, the spin builds |
| 2 → 1 | 10 m, 0 m/s | at 7.6 m or above | 1.6 s | +0 m | 0.19 Wh | B to centre, A takes the weight as the spin dies |
| 2 → 3 | 10 m, 0 m/s | spinning | 2.5 s | +0 m | 0.11 Wh | disc tilted, speeding up |
| 3 → 2 | 10 m, 4 m/s | spinning | 2.5 s | +0 m | 0.11 Wh | disc levelled, slowing |
| 3 → 4 | 10 m, 4 m/s | from 10 m: the pitch-over's loss over the 10 m margin | 4.9 s | +0 m | 0.86 Wh | B to centre as the spin dies, pitch over to wing-borne |
| 4 → 1 | 10 m, 18 m/s | A holds the weight at the top, and the stint on A under 20 s | 7.9 s | -0 m | 0.98 Wh | pitch up until A points up |
| 4 → 3 | 10 m, 18 m/s | from 10 m | 3.8 s | +6 m | 0.00 Wh | forced pull-up, the inflow spins it up |

Any other move goes along these: 1 to 4 is 1 → 2 → 3 → 4; 4 to 2 is 4 → 3 → 2.

## Sorties

**Launch, from the deck or the water to wing-borne:** 15 s, 2.01 Wh, 6 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 1 | mode 1 climb | 5.1 s | 0 → 8 m | 0.75 Wh |
| 1 | B off centre, the spin builds | 1.3 s | 8 → 8 m | 0.20 Wh |
| 2 | mode 2 climb | 1.2 s | 8 → 10 m | 0.09 Wh |
| 2 | disc tilted, speeding up | 2.5 s | 10 → 10 m | 0.11 Wh |
| 3 | B to centre as the spin dies, pitch over to wing-borne | 4.9 s | 10 → 10 m | 0.86 Wh |

**Recovery, from wing-borne back aboard:** 17 s, 1.48 Wh, 9 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | forced pull-up, the inflow spins it up | 3.8 s | 10 → 16 m | 0.00 Wh |
| 3 | disc levelled, slowing | 0.0 s | 16 → 16 m | 0.00 Wh |
| 2 | mode 2 descent | 4.3 s | 16 → 8 m | 0.22 Wh |
| 2 | B to centre, A takes the weight as the spin dies | 1.6 s | 8 → 8 m | 0.19 Wh |
| 1 | mode 1 descent | 7.6 s | 8 → 0 m | 1.07 Wh |

**Recovery straight from 4 to 1, tried (from 10 m, as low as the pitch-up allows):** 18 s, 2.37 Wh, 18 s of it on A, carrying the weight.

| Mode | What | Time | Height | Energy |
|---|---|---|---|---|
| 4 | pitch up until A points up | 7.9 s | 10 → 10 m | 0.98 Wh |
| 1 | mode 1 descent | 10.0 s | 10 → 0 m | 1.40 Wh |

The pitch-up from 18 m/s takes 7.9 s and 58 m, loses 0.3 m, and ends hovering on A at 0.77 × its burst. It works; it just keeps A at its burst, low, for the whole stint.

## A alone, or A with A2

| | A alone | A and A2 |
|---|---|---|
| Mass | 2.93 kg | 3.00 kg |
| Motors | 0.15 kg: A 423 W | 0.22 kg: A 332 W, A2 154 W |
| Mode 1 hover | 428 W | 313 W |
| Pitch-over (3 → 4): height lost | -0 m | -0 m |
| Launch + recovery | 3.5 Wh | 2.9 Wh |
| One motor out in mode 1 | falls | holds 1.47 × the weight |

Mode 1 is the exposure: 16 s a sortie at or under 7.6 m with A alone carrying the weight. Three motors can't lose one, and a fall from 7.6 m takes 1.2 s, less than the 1.3 s B needs to turn it into a spin: it hits at 12 m/s. With A2, five of six props are left to hold it.

## A motor out, mode by mode

- **2 and 3, spinning:** at the burst, one motor holds the spinning hover; with none, it comes down like a seed at 3.2 m/s, and the spin holds 5.7× the sink's energy to flare with.
- **4, wing-borne:** a glider; the forced pull-up (4 → 3) leads to the same seed fall.
- **1, under 7.6 m:** see above.

The spin building and dying, A's and B's authority, the wind in modes 1 and 2, and floating are in `dynamics.md` and `water.md`. Not modelled: closed-loop stability in each mode, and the deck's motion.
