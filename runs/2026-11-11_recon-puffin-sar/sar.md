# The spar Puffin, SAR build: mass, power and missions

First-order numbers for the SAR layout (`recon/puffin_sar.py`, inputs in `design/recon/puffin.toml` [layouts.sar] and [sar]). Estimates to build from; the hover rig and first flights replace them.

## Mass

| Part | kg |
|---|---|
| hull | 1.59 |
| battery | 3.50 |
| payload | 0.50 |
| avionics | 0.85 |
| fins | 0.30 |
| wing | 1.10 |
| motor | 0.60 |
| prop | 0.28 |
| drop pack | 0.40 |
| **total** | **9.12** |

## Afloat and knocked over

| | Mass | Under water | Props clear | Dome above water | Battery travel | GZ at 15° | Least GZ | GZ at 90° | Rights itself |
|---|---|---|---|---|---|---|---|---|---|
| drop pack aboard | 9.12 kg | 52 cm | 43 cm | 78 cm | 47 cm | +1.2 cm | +0.4 cm | +40 cm | yes |
| after the drop | 8.72 kg | 52 cm | 43 cm | 78 cm | 47 cm | +1.1 cm | +0.4 cm | +41 cm | yes |

## Hover and cruise

- Disc loading 5.8 kg/m² on the two props; hover 780 W electric, 390 W a motor; at 1.6× thrust to weight each motor peaks near 790 W.
- Wing loading 21.9 kg/m²: stalls at 17.1 m/s, cruises at 22.2 m/s (43 kn) on 578 W; drag area 302 cm².
- Pack 665 Wh, 532 Wh usable. Launch and landing in hover 26 Wh. Then 52 min of cruise, 70 km.
- Afloat on a full pack, marking at 6 W: 89 h.

| Airspeed | Electric power |
|---|---|
| 18.8 m/s | 453 W |
| 22.2 m/s | 578 W |
| 25.6 m/s | 763 W |
| 28.9 m/s | 1015 W |

## The missions

Launch, fly to the datum and search, then land beside the person to mark them, or fly back the same way. Search time is what the usable pack affords after the hover and the transit; afloat is what is left for marking if it searches for the mission's whole task time.

| Mission | Out | Task time | Search it affords, then marking | Then afloat | Search it affords, then flying back |
|---|---|---|---|---|---|
| MOB 3 km astern, sea state 3, 15 kn wind | 3 km, 2 min | 30 min | 50 min | 33 h | 48 min |
| MOB 10 km astern, sea state 4, 20 kn wind | 10 km, 7 min | 120 min | 45 min | none: the search runs the pack down | 38 min |

## Forward sweep

The wing swept forward with its mean chord where the SAR layout has it, so the neutral point stays put: the tips and props go up the hull, the root down. Up the hull the props sit beside the narrowing dome, so they can be longer (to the hull with a gap, or tip to tip, or the cap). Hover power with those props, and with the original 0.76 m props for comparison. The SAR build itself flies 25° and 1.0 m props, a little short of the longest.

| Sweep | Root LE | Props' plane | Longest props | Disc loading | Hover | Hover, 0.76 m props | Mass | Battery travel | Props clear | Clear, rolled 15° | GZ at 15° | Least GZ | Rights itself |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0° | 70 cm | 82 cm | 1.09 m | 4.9 kg/m² | 722 W | 1035 W | 9.17 kg | 50 cm | 30 cm | 16 cm | +1.5 cm | +0.5 cm | yes |
| 15° | 62 cm | 90 cm | 1.09 m | 4.9 kg/m² | 722 W | 1035 W | 9.17 kg | 48 cm | 37 cm | 23 cm | +1.3 cm | +0.4 cm | yes |
| 25° | 57 cm | 95 cm | 1.09 m | 4.9 kg/m² | 722 W | 1035 W | 9.17 kg | 46 cm | 43 cm | 29 cm | +1.2 cm | +0.4 cm | yes |
| 35° | 50 cm | 102 cm | 1.09 m | 4.9 kg/m² | 719 W | 1036 W | 9.17 kg | 45 cm | 50 cm | 36 cm | +1.0 cm | +0.3 cm | yes |
| 45° | 41 cm | 111 cm | 1.13 m | 4.6 kg/m² | 700 W | 1039 W | 9.19 kg | 42 cm | 58 cm | 44 cm | +0.7 cm | +0.3 cm | yes |

## Power lost in flight

With the screw unpowered the battery runs down the boom and the craft pitches up to tail-first. With the motors still running that is only its hover attitude, and it lands. With all power gone it falls boom first: the speed it meets the water at, and the drop height that equals.

| Slowed by | Hits the water at | Like a drop of | Adds |
|---|---|---|---|
| nothing: it falls boom first | 50.3 m/s | 129.0 m | nothing |
| the props windmilling (1.00 m) | 13.2 m/s | 8.8 m | nothing |
| the longest props windmilling (1.13 m) | 11.7 m/s | 7.0 m | nothing |
| autorotating, collective pitch (1.00 m), then a flare | 8.4 m/s, 0.0 m/s after the flare | 3.6 m, 0.0 m | variable-pitch hubs on both props |
| autorotating, the longest props (1.13 m), then a flare | 7.5 m/s, 0.0 m/s after the flare | 2.8 m, 0.0 m | variable-pitch hubs on both props |
| a 2.5 m parachute | 5.1 m/s | 1.3 m | 0.5 kg |
