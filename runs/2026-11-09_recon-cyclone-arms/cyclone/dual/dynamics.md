# The Cyclone's spin, control and wind: dual

Blade elements along each arm (a symmetric section, linear to its stall at 9.0° and a flat plate past it), the inflow from momentum theory ring by ring. REF inputs in `[dynamics]` of `design/recon/cyclone.toml`.

## The spin setting

To carry the weight at 217 rpm the arms sit at **15.2°** to the spin plane: B turns each 74.8° off centre. The tips meet the air at 6.3°, 2.8° under the stall. The blade elements' hover power, 68 W into the air, matches the rotor model's 63 W.

## The spin building and dying

B turns at 60°/s. Building (1 → 2), A gives what holds the height, up to its burst, and B turns as far each step as the height allows. Dying (2 → 1), B turns back as fast as A, up to its burst, can take the weight; past centre it turns A 15° against the spin to finish it.

| | 1 → 2, the spin builds | 2 → 1, the spin dies |
|---|---|---|
| Time | **1.36 s** | **1.57 s** |
| B | 0° to 75°: 1.25 s at its slew | 75° to -15° and back |
| Height | +0.05 m at most | +0.05 m at most |
| A, of its burst | 100% at most | 88% at most |
| Energy | 0.13 Wh | 0.12 Wh |

Both fit well inside the 3 s the modes' manager allowed for each. The spin builds about as fast as B can turn, so B's slew sets it, not A; the arms, broadside to their own motion, stop the spin in about the same time.

## Control: what A and B can do

Spin inertia 0.21 kg m²; A's thrust lags its PWM by 50 ms.

| Mode | Axis | By | Can do |
|---|---|---|---|
| 1 lift-off | roll, pitch | A, one up and two down | 2.9 N m: tilts 20° in 0.23 s |
| | yaw | B, all three A tilted 15° | 5.0 N m, 1335°/s² |
| 2 spinning | disc tilt | B's cyclic once a turn (3.6 Hz) | ±2.6° (the stall leaves 2.6°, B's bandwidth passes 91% of 6°): 3.4 N m, tilting the disc at **41°/s** against the spin's 4.8 kg m²/s |
| | sideways | A's PWM once a turn, ±30% | 0.36 N, the push of a 0.9° lean; the disc tilt it gives, 1.0°/s, is nothing |
| 4 wing-borne | pitch | A, the fin's motor below against the wings' above | trims with 39% of the thrust on the fin's motor at 17 m/s (static margin 5%); 2.8 N m nose up beyond, 9 N m at full power |
| | yaw | A, one wing's motor against the other | 2.6 N m at cruise thrust |
| | roll | B, all three arms twisted the same way | 146°/s for 5° of twist at 17 m/s (126°/s at 14); 30° of bank in 0.24 s |

Mode 4: twisting the fin alone gives a side force but no yaw: it sits at the CG's station along the flight path, with nothing behind it. So yaw and pitch are A's (the fine control), roll and lift B's (the large), as the modes say. Rolling in mode 4 is turning about the old spin axis, so the three arms damp it as they damp the spin.

Mode 2: B steers. A's PWM once a turn barely tilts the disc (its thrust is nearly in the spin plane) but pushes the whole bird sideways, which helps hold station without tilting.

## Wind

**Mode 1**, B centred: the arms stand chord-up, three flat plates whose pushes add to 1.5 arms' along the wind. Leaning into it on A's burst, it holds station up to **10.2 m/s**.

**Mode 2**, spinning: the advancing arm meets the air faster than the retreating one; B's cyclic trims the roll out, the retreating arm's angle of attack climbing toward the stall. It holds station up to **3.50 m/s**, where the retreating arm stalls, with 4.1° of cyclic and the disc tilted 0.2° into the wind; the power falls from 131 W in still air to 92 W there (the wind's lift).

The retreating arm limits mode 3 the same way: its top speed is now 3.50 m/s, an advance ratio of 0.18 (it was taken as 0.35, 6.8 m/s).

A 1 m/s gust, before B answers, tips the disc at 22°/s; B's cyclic tilts it at 41°/s, so it answers gusts of up to 1.9 m/s.

| Wind | Mode 1: lean, A of its burst | Mode 2: cyclic, retreating arm, power |
|---|---|---|
| 0 m/s (ss0) | 0°, 77% | 0.0°, 6.3°, 131 W |
| 2 m/s (ss1) | 2°, 77% | 2.6°, 7.8°, 112 W |
| 5 m/s (ss2) | 11°, 78% | ✗ can't hold station |
| 8 m/s (ss3) | 27°, 86% | ✗ can't hold station |
| 11 m/s (ss4) | 44°, 107% ✗ | ✗ can't hold station |
| 14 m/s (ss5) | 57°, 142% ✗ | ✗ can't hold station |

**Spinning faster** lowers the arms' mean lift coefficient for the same thrust and leaves the retreating arm more of the stall, at the price of more power and a bigger motor (the design held as it is):

| Mean lift coefficient | rpm | Hover | Spinning peak (A rated 293 W) | Mode 2 wind limit |
|---|---|---|---|---|
| 0.30 | 294 | 175 W | 354 W | 10.00 m/s |
| 0.35 | 272 | 157 W | 317 W | 8.50 m/s |
| 0.40 | 254 | 144 W | 291 W | 7.00 m/s |
| 0.45 | 240 | 135 W | 273 W | 5.75 m/s |
| 0.50 | 227 | 128 W | 258 W | 4.50 m/s |
| 0.55 (now) | 217 | 122 W | 247 W | 3.50 m/s |

Not modelled: closed-loop stability in each mode, the arms flexing, gust dynamics beyond the first moment, and the wind's lift on the arms in mode 1 as it leans.
