# The spar Puffin: will it always bob back tail-down?

A UAS-sized Puffin (NASA's electric tailsitter, Moore 2010), floated tail-down and knocked over by every angle to 180°, onto its belly or back and onto a wingtip. GZ is the righting arm: above zero it pushes it back upright. It always rights itself if GZ stays above zero all the way round (`recon/puffin.py`, inputs in `design/recon/puffin.toml`).

## The layouts

| Layout | Mass | Battery afloat | Under water | Props clear | Dome above water | Rights itself | GZ at 15°, least | GZ at 90° |
|---|---|---|---|---|---|---|---|---|
| Puffin as drawn: a slender streamlined hull, the battery and avionics mid-hull, the CG on the wing | 6.96 kg | 60 cm up | 48 cm | 37 cm | 82 cm | no: falls from 5° onto its belly or back | -7.5, -24.7 cm | +13 cm |
| Spar, fixed: battery and 1 kg of ballast in the boom; the CG 1.25 chords behind the wing, the tail lifting | 8.52 kg | 10 cm up | 53 cm | 27 cm | 77 cm | yes | +2.3, +0.8 cm | +48 cm |
| Spar, screw: the battery runs down the boom to float, up to the wing to fly; a normal tail | 7.52 kg | 10 cm up | 51 cm | 31 cm | 79 cm | yes | +0.3, +0.1 cm | +43 cm |

## The battery on a screw

The screw layout with the wing's leading edge at each station, each payload in the dome and with or without ballast in the boom. Afloat the battery sits 10 cm up from the tail; in flight it runs up to balance the craft on the wing with a 10 % static margin. Travel: how far the screw runs between the two.

| Wing LE | Dome payload | Ballast | Mass | Battery in flight | Travel | Props clear | Rights itself | GZ at 15°, least |
|---|---|---|---|---|---|---|---|---|
| 0.60 m | 0.3 kg | 0.0 kg | 7.52 kg | 43 cm up | 33 cm | 21 cm | yes | +0.9, +0.3 cm |
| 0.60 m | 0.3 kg | 0.5 kg | 8.02 kg | 51 cm up | 41 cm | 20 cm | yes | +1.9, +0.6 cm |
| 0.60 m | 0.6 kg | 0.0 kg | 7.82 kg | 36 cm up | 26 cm | 20 cm | yes | +0.3, +0.1 cm |
| 0.60 m | 0.6 kg | 0.5 kg | 8.32 kg | 44 cm up | 34 cm | 20 cm | yes | +1.3, +0.4 cm |
| 0.60 m | 1.0 kg | 0.0 kg | 8.22 kg | 27 cm up | 17 cm | 20 cm | no: falls from 5° onto its wingtip | -0.3, -0.8 cm |
| 0.60 m | 1.0 kg | 0.5 kg | 8.72 kg | 35 cm up | 25 cm | 19 cm | yes | +0.6, +0.2 cm |
| 0.70 m | 0.3 kg | 0.0 kg | 7.52 kg | 62 cm up | 52 cm | 31 cm | yes | +0.3, +0.1 cm |
| 0.70 m | 0.3 kg | 0.5 kg | 8.02 kg | 71 cm up | 61 cm | 30 cm | yes | +1.3, +0.4 cm |
| 0.70 m | 0.6 kg | 0.0 kg | 7.82 kg | 56 cm up | 46 cm | 30 cm | no: falls from 5° onto its belly or back | -0.3, -0.5 cm |
| 0.70 m | 0.6 kg | 0.5 kg | 8.32 kg | 66 cm up | 56 cm | 30 cm | yes | +0.7, +0.2 cm |
| 0.70 m | 1.0 kg | 0.0 kg | 8.22 kg | 48 cm up | 38 cm | 30 cm | no: falls from 5° onto its wingtip | -0.9, -2.4 cm |
| 0.70 m | 1.0 kg | 0.5 kg | 8.72 kg | 58 cm up | 48 cm | 29 cm | yes | +0.1, +0.0 cm |
| 0.80 m | 0.3 kg | 0.0 kg | 7.52 kg | 81 cm up | 71 cm | 41 cm | no: falls from 5° onto its wingtip | -0.4, -0.7 cm |
| 0.80 m | 0.3 kg | 0.5 kg | 8.02 kg | 92 cm up | 82 cm | 40 cm | yes | +0.7, +0.2 cm |
| 0.80 m | 0.6 kg | 0.0 kg | 7.82 kg | 76 cm up | 66 cm | 40 cm | no: falls from 5° onto its belly or back | -0.9, -2.2 cm |
| 0.80 m | 0.6 kg | 0.5 kg | 8.32 kg | 87 cm up | 77 cm | 40 cm | yes | +0.2, +0.1 cm |
| 0.80 m | 1.0 kg | 0.0 kg | 8.22 kg | 70 cm up | 60 cm | 40 cm | no: falls from 5° onto its wingtip | -1.5, -4.1 cm |
| 0.80 m | 1.0 kg | 0.5 kg | 8.72 kg | 81 cm up | 71 cm | 39 cm | no: falls from 5° onto its belly or back | -0.5, -1.3 cm |
| 0.90 m | 0.3 kg | 0.0 kg | 7.52 kg | 100 cm up | 90 cm | 51 cm | no: falls from 5° onto its wingtip | -1.0, -2.4 cm |
| 0.90 m | 0.3 kg | 0.5 kg | 8.02 kg | 113 cm up | 103 cm | 50 cm | yes | +0.1, +0.0 cm |
| 0.90 m | 0.6 kg | 0.0 kg | 7.82 kg | 96 cm up | 86 cm | 50 cm | no: falls from 5° onto its wingtip | -1.5, -4.0 cm |
| 0.90 m | 0.6 kg | 0.5 kg | 8.32 kg | 109 cm up | 99 cm | 50 cm | no: falls from 5° onto its wingtip | -0.4, -1.1 cm |
| 0.90 m | 1.0 kg | 0.0 kg | 8.22 kg | 91 cm up | 81 cm | 50 cm | no: falls from 5° onto its belly or back | -2.1, -5.9 cm |
| 0.90 m | 1.0 kg | 0.5 kg | 8.72 kg | 104 cm up | 94 cm | 49 cm | no: falls from 5° onto its belly or back | -1.0, -2.9 cm |
