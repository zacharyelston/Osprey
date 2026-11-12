# The Trident in MuJoCo, afloat

MuJoCo carries the rigid body; the water is ours: each step the sealed meshes are clipped at the surface and the pressure under it is summed into a force and a torque (`src/osprey/trident_sim.py`). Damping is 20 % of critical in heave and 10 % in roll, both REF stand-ins; added mass, wave radiation and breaking waves aren't modelled. The props are stopped.

## Dropped in calm water

Let go at rest, knocked over by each angle, in two directions: toward a module (0°) and between two (60°). *Settles* is when it is last more than 10° off upright; *swings to* is the most it tilts again after first coming upright.

| Craft | GM | Roll period | Let go at | Toward | Comes back | Settles | Swings to |
|---|---|---|---|---|---|---|---|
| Balanced | 3.1 m | 1.5 s | 30° | 0° | yes | 1.5 s | 16° |
| Balanced | 3.1 m | 1.5 s | 30° | 60° | yes | 1.2 s | 10° |
| Balanced | 3.1 m | 1.5 s | 60° | 0° | yes | 2.7 s | 21° |
| Balanced | 3.1 m | 1.5 s | 60° | 60° | yes | 2.3 s | 14° |
| Balanced | 3.1 m | 1.5 s | 90° | 0° | yes | 4.3 s | 22° |
| Balanced | 3.1 m | 1.5 s | 90° | 60° | no: stays at 92° |  |  |
| Balanced | 3.1 m | 1.5 s | 120° | 0° | yes | 4.2 s | 24° |
| Balanced | 3.1 m | 1.5 s | 120° | 60° | no: stays at 92° |  |  |
| Balanced | 3.1 m | 1.5 s | 150° | 0° | yes | 4.2 s | 25° |
| Balanced | 3.1 m | 1.5 s | 150° | 60° | yes | 3.5 s | 16° |
| Balanced | 3.1 m | 1.5 s | 175° | 0° | yes | 4.7 s | 28° |
| Balanced | 3.1 m | 1.5 s | 175° | 60° | yes | 4.2 s | 16° |
| Found | 5.9 m | 1.1 s | 30° | 0° | yes | 1.4 s | 13° |
| Found | 5.9 m | 1.1 s | 30° | 60° | yes | 0.7 s | 9° |
| Found | 5.9 m | 1.1 s | 60° | 0° | yes | 2.8 s | 16° |
| Found | 5.9 m | 1.1 s | 60° | 60° | yes | 1.7 s | 9° |
| Found | 5.9 m | 1.1 s | 90° | 0° | yes | 3.5 s | 17° |
| Found | 5.9 m | 1.1 s | 90° | 60° | yes | 3.4 s | 9° |
| Found | 5.9 m | 1.1 s | 120° | 0° | yes | 3.3 s | 19° |
| Found | 5.9 m | 1.1 s | 120° | 60° | yes | 3.0 s | 11° |
| Found | 5.9 m | 1.1 s | 150° | 0° | yes | 3.7 s | 21° |
| Found | 5.9 m | 1.1 s | 150° | 60° | yes | 2.3 s | 10° |
| Found | 5.9 m | 1.1 s | 175° | 0° | yes | 4.5 s | 24° |
| Found | 5.9 m | 1.1 s | 175° | 60° | yes | 3.7 s | 10° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 30° | 0° | yes | 1.2 s | 12° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 30° | 60° | yes | 0.6 s | 8° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 60° | 0° | yes | 2.2 s | 15° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 60° | 60° | yes | 1.5 s | 10° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 90° | 0° | yes | 2.9 s | 16° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 90° | 60° | yes | 3.3 s | 10° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 120° | 0° | yes | 3.0 s | 18° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 120° | 60° | yes | 2.8 s | 11° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 150° | 0° | yes | 3.3 s | 20° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 150° | 60° | yes | 2.7 s | 11° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 175° | 0° | yes | 4.1 s | 22° |
| Found, glass/foam sandwich 25 mm | 6.9 m | 1.0 s | 175° | 60° | yes | 3.6 s | 12° |

## Riding regular waves

Upright at rest, a regular wave along x ramped in over 10 s, then 120 s ridden. Steepness is height over length (1/7 breaks). Clearances are the lowest point of any prop's rim and of the core's floor edge above the local surface.

| Craft | Height | Length | Period | Steepness | Heading | Most tilt | Over 30° | Props clear by | Floor clears by |
|---|---|---|---|---|---|---|---|---|---|
| Found | 0.5 m | 10 m | 2.5 s | 1/20 | 0° | 7° | 0 % | -0.10 m | -0.09 m |
| Found | 0.5 m | 10 m | 2.5 s | 1/20 | 60° | 6° | 0 % | +0.10 m | -0.08 m |
| Found | 0.5 m | 5 m | 1.8 s | 1/10 | 0° | 20° | 0 % | -0.63 m | -0.37 m |
| Found | 0.5 m | 5 m | 1.8 s | 1/10 | 60° | 15° | 0 % | -0.35 m | -0.40 m |
| Found | 1.0 m | 20 m | 3.6 s | 1/20 | 0° | 9° | 0 % | +0.18 m | -0.04 m |
| Found | 1.0 m | 20 m | 3.6 s | 1/20 | 60° | 10° | 0 % | +0.28 m | -0.02 m |
| Found | 1.0 m | 10 m | 2.5 s | 1/10 | 0° | 29° | 0 % | -1.33 m | -0.43 m |
| Found | 1.0 m | 10 m | 2.5 s | 1/10 | 60° | 16° | 0 % | -0.65 m | -0.12 m |
| Found | 2.0 m | 40 m | 5.1 s | 1/20 | 0° | 9° | 0 % | +0.38 m | -0.04 m |
| Found | 2.0 m | 40 m | 5.1 s | 1/20 | 60° | 9° | 0 % | +0.44 m | -0.03 m |
| Found | 2.0 m | 20 m | 3.6 s | 1/10 | 0° | 19° | 0 % | -0.94 m | -0.24 m |
| Found | 2.0 m | 20 m | 3.6 s | 1/10 | 60° | 18° | 0 % | -0.89 m | -0.23 m |
| Found | 3.0 m | 60 m | 6.2 s | 1/20 | 0° | 9° | 0 % | +0.47 m | -0.04 m |
| Found | 3.0 m | 60 m | 6.2 s | 1/20 | 60° | 9° | 0 % | +0.51 m | -0.04 m |
| Found | 3.0 m | 30 m | 4.4 s | 1/10 | 0° | 19° | 0 % | -0.17 m | -0.15 m |
| Found | 3.0 m | 30 m | 4.4 s | 1/10 | 60° | 20° | 0 % | -0.22 m | -0.15 m |
| Found | 4.0 m | 80 m | 7.2 s | 1/20 | 0° | 9° | 0 % | +0.51 m | -0.04 m |
| Found | 4.0 m | 80 m | 7.2 s | 1/20 | 60° | 9° | 0 % | +0.54 m | -0.04 m |
| Found | 4.0 m | 40 m | 5.1 s | 1/10 | 0° | 19° | 0 % | -0.05 m | -0.15 m |
| Found | 4.0 m | 40 m | 5.1 s | 1/10 | 60° | 20° | 0 % | -0.06 m | -0.14 m |
| Found, glass/foam sandwich 25 mm | 0.5 m | 10 m | 2.5 s | 1/20 | 0° | 6° | 0 % | -0.02 m | -0.02 m |
| Found, glass/foam sandwich 25 mm | 0.5 m | 10 m | 2.5 s | 1/20 | 60° | 5° | 0 % | +0.17 m | -0.00 m |
| Found, glass/foam sandwich 25 mm | 0.5 m | 5 m | 1.8 s | 1/10 | 0° | 18° | 0 % | -0.52 m | -0.29 m |
| Found, glass/foam sandwich 25 mm | 0.5 m | 5 m | 1.8 s | 1/10 | 60° | 8° | 0 % | +0.19 m | -0.19 m |
| Found, glass/foam sandwich 25 mm | 1.0 m | 20 m | 3.6 s | 1/20 | 0° | 8° | 0 % | +0.14 m | +0.04 m |
| Found, glass/foam sandwich 25 mm | 1.0 m | 20 m | 3.6 s | 1/20 | 60° | 9° | 0 % | +0.13 m | +0.05 m |
| Found, glass/foam sandwich 25 mm | 1.0 m | 10 m | 2.5 s | 1/10 | 0° | 30° | 0 % | -1.49 m | -0.30 m |
| Found, glass/foam sandwich 25 mm | 1.0 m | 10 m | 2.5 s | 1/10 | 60° | 14° | 0 % | -0.60 m | -0.08 m |
| Found, glass/foam sandwich 25 mm | 2.0 m | 40 m | 5.1 s | 1/20 | 0° | 9° | 0 % | +0.34 m | +0.03 m |
| Found, glass/foam sandwich 25 mm | 2.0 m | 40 m | 5.1 s | 1/20 | 60° | 9° | 0 % | +0.40 m | +0.04 m |
| Found, glass/foam sandwich 25 mm | 2.0 m | 20 m | 3.6 s | 1/10 | 0° | 18° | 0 % | -0.40 m | -0.08 m |
| Found, glass/foam sandwich 25 mm | 2.0 m | 20 m | 3.6 s | 1/10 | 60° | 18° | 0 % | -0.53 m | -0.08 m |
| Found, glass/foam sandwich 25 mm | 3.0 m | 60 m | 6.2 s | 1/20 | 0° | 9° | 0 % | +0.43 m | +0.03 m |
| Found, glass/foam sandwich 25 mm | 3.0 m | 60 m | 6.2 s | 1/20 | 60° | 9° | 0 % | +0.47 m | +0.04 m |
| Found, glass/foam sandwich 25 mm | 3.0 m | 30 m | 4.4 s | 1/10 | 0° | 18° | 0 % | -0.20 m | -0.08 m |
| Found, glass/foam sandwich 25 mm | 3.0 m | 30 m | 4.4 s | 1/10 | 60° | 19° | 0 % | -0.24 m | -0.08 m |
| Found, glass/foam sandwich 25 mm | 4.0 m | 80 m | 7.2 s | 1/20 | 0° | 9° | 0 % | +0.47 m | +0.03 m |
| Found, glass/foam sandwich 25 mm | 4.0 m | 80 m | 7.2 s | 1/20 | 60° | 9° | 0 % | +0.50 m | +0.04 m |
| Found, glass/foam sandwich 25 mm | 4.0 m | 40 m | 5.1 s | 1/10 | 0° | 18° | 0 % | -0.03 m | -0.07 m |
| Found, glass/foam sandwich 25 mm | 4.0 m | 40 m | 5.1 s | 1/10 | 60° | 18° | 0 % | -0.04 m | -0.07 m |
