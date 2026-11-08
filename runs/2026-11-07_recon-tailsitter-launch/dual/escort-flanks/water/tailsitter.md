# Tailsitter on the water: escort-flanks, dual

2.22 kg, 140 cm span. Two 30 cm tractor props (537 W peak in all, 0.16 kg of motors), four float pods on struts. REF inputs in `[hover]` and `[floats]` of `design/recon/airframes/tailsitter.toml`.

| Requirement | Spec | This bird | |
|---|---|---|---|
| Floats upright on its pods, the wing clear | pods only | draft 8.8 cm; in the water: float_strut_-1, float_strut_1, float_tip_-1, float_tip_1 | ✓ |
| Reserve buoyancy | ≥ 2.0 | 5.7 | ✓ |
| Props above the water | ≥ 30 cm | 49 cm | ✓ |
| Cameras above the water | > 0 | 29 cm | ✓ |
| Stays upright: GM tipping across the span / along it | ≥ 3 cm | 133 / 256 cm | ✓ |
| Natural periods, across / along | away from the waves' 2–9 s | 0.19 / 0.29 s | ✓ |
| Launch: throttle-up to wing-borne | ≤ 15 s | 4.2 s (clear of the water 0.36 s, 3 m up 2.1 s) | ✓ |
| Lowest point in the pitch-over | > 1 m above the water | 3.0 m | ✓ |
| Surface tension at the waterline | | 0.09 N, 0.4% of the weight | |
| Thrust, weight, buoyancy at the start | | 35 N, 22 N, 22 N | |
| Landing: settling onto the pods at 1.5 m/s | ≤ 3.0 g (sized for) | 2.3 g | ✓ |
| Hover energy per sortie (launch and landing) | | 3.9 Wh at 312 W | |
| Strongest wind it can hover in, broadside | | 11.9 m/s (leaning on its thrust margin) | |

The sea, for a vertical launch:
- The design wave (the highest in a hundred) tips the bird by its slope, and lifts the water under it at its surface speed, which the climb out has to beat.
- The wind, broadside to the upright wing, heels it afloat. Its sail (42 cm above the pods' grip) is held only by GM across the span.
- The launch needs the slope and the heel together under 30°, and a wind it can hover in.

| Sea state | H_s, T_p | Typical wind | Wave slope | Heel in the wind | GM it would need | Surface speed | Launch |
|---|---|---|---|---|---|---|---|
| 0 | 0 m, 2 s | 0 m/s | 0.0° | 0° | 0 cm | 0.00 m/s | ✓ |
| 1 | 0.05 m, 2 s | 2 m/s | 2.4° | 1° | 3 cm | 0.13 m/s | ✓ |
| 2 | 0.3 m, 3.5 s | 5 m/s | 4.7° | 4° | 19 cm | 0.45 m/s | ✓ |
| 3 | 0.9 m, 5 s | 8 m/s | 6.9° | 10° | 55 cm | 0.94 m/s | ✓ |
| 4 | 1.9 m, 7 s | 11 m/s | 7.4° | 18° | 106 cm | 1.42 m/s | ✓ |
| 5 | 3.2 m, 9 s | 14 m/s | 7.6° | 28° | 173 cm | 1.87 m/s | ✗ |
