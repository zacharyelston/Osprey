# The Trident: a three-module tailsitter, by the numbers

Three identical modules (an arm and wing panel, a motor pod and a big slow prop, a leg and its foot) round a foam-walled core sized to a 4x8 ft sheet, the power cells in a bay a metre long under it. It lifts off on its tail, flies on the three wings in a Y and lands back on its feet (`src/osprey/trident.py`, inputs in `design/trident.toml`, every number a REF stand-in).

Each is sized for one trip: 4 min of hover (two lift-offs and landings), 50 km of cruise, and 10 min of cruise in reserve. Knocked over by every angle to 180°, toward a module, between two and halfway; heights are up the axis from the bay's tail.

## Three layouts

| Layout | Max weight | CG | Props' plane | Static margin | Hover | Cruise | Waterline | GM | Props clear the water | Rights itself | Least GZ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| As sketched: the module ring at the core's top | 1112 kg | 1.83 m | 3.80 m | -1.52 | 161 kW | 105 kW at 52 m/s | 0.99 m | -1.2 m | 2.81 m | no: past 5° (60° round) | -46 cm |
| Balanced: the sketch with the module ring slid down until it flies | 1068 kg | 1.46 m | 1.81 m | +0.10 | 152 kW | 96 kW at 51 m/s | 0.84 m | 3.1 m | 0.96 m | no: past 70° (60° round) | -23 cm |
| Found: balanced, a glass skin, legs with pads, longer and narrower wings, the person crouched | 888 kg | 1.38 m | 1.70 m | +0.10 | 115 kW | 65 kW at 49 m/s | 0.96 m | 5.9 m | 0.74 m | yes | +4 cm |

Static margin is in wing chords, the CG ahead of the wing's quarter chord; it must be positive to fly.

## The found layout, crewed and as cargo

| | Crewed | Cargo |
|---|---|---|
| What it carries | 195 kg: a person and 100 kg | 246 kg of cargo |
| Max weight | 888 kg | 888 kg |
| Battery | 41 kWh, 204 kg, 13 % of the bay | same |
| Hover / installed | 115 / 190 kW | same |
| Disc loading, downwash | 18 kg/m², 8.5 m/s | same |
| Cruise | 49 m/s on 65 kW, L/D 10.2 (stall 39 m/s) | same |
| Static margin | +0.10 | +0.08 |
| Afloat: waterline, the core's floor above it | 0.96 m, 4 cm | 0.96 m, 4 cm |
| GM, props clear the water | 5.9 m, 0.74 m | 6.0 m, 0.74 m |
| Rights itself, least GZ | yes, +4 cm | yes, +5 cm |

Across the prop tips it is 10.8 m; the wing tips are 10.4 m apart in plan; it stands 4.6 m tall on its feet. Each prop's tip clears the core by 6 cm and the next tip by 0.86 m.

## Where the weight goes

| Part | Crewed | Cargo | Up the axis |
|---|---|---|---|
| person | 95 kg | 0 kg | 1.68 m |
| mission load | 100 kg | 0 kg | 1.68 m |
| container | 20 kg | 0 kg | 1.68 m |
| seat | 8 kg | 0 kg | 1.48 m |
| hatch | 15 kg | 0 kg | 2.70 m |
| safety | 8 kg | 0 kg | 1.68 m |
| core walls | 116 kg | 116 kg | 2.40 m |
| core frame | 45 kg | 45 kg | 1.40 m |
| flotation | 0 kg | 0 kg | 1.48 m |
| nose | 5 kg | 5 kg | 4.03 m |
| bay | 16 kg | 16 kg | 0.50 m |
| battery | 204 kg | 204 kg | 0.45 m |
| motors | 38 kg | 38 kg | 1.55 m |
| props | 42 kg | 42 kg | 1.70 m |
| pods | 15 kg | 15 kg | 1.40 m |
| wings | 95 kg | 95 kg | 1.17 m |
| legs | 14 kg | 14 kg | 0.65 m |
| float-feet | 0 kg | 0 kg | -0.10 m |
| avionics | 52 kg | 52 kg | 1.30 m |
| cargo | | 246 kg | 1.68 m |
| **total** | **888 kg** | **888 kg** | CG 1.38 / 1.37 m |

## The props

| Prop | Across the tips | Max weight | Hover | Disc loading | Downwash | Cruise |
|---|---|---|---|---|---|---|
| 3.05 m | 7.8 m | 988 kg | 202 kW | 45 kg/m² | 13.4 m/s | 115 kW at 61 m/s |
| 3.66 m | 9.0 m | 919 kg | 151 kW | 29 kg/m² | 10.8 m/s | 86 kW at 54 m/s |
| 4.57 m | 10.8 m | 888 kg | 115 kW | 18 kg/m² | 8.5 m/s | 65 kW at 49 m/s |

## The core's walls

| Skin | Walls | Core walls weigh | Max weight | Battery |
|---|---|---|---|---|
| foam walls wrapped in HDPE, 3 mm each face | 15 cm | 155 kg | 944 kg | 43 kWh |
| foam walls wrapped in HDPE, 3 mm each face | 20 cm | 192 kg | 1018 kg | 49 kWh |
| foam walls in a glass-epoxy skin, a sandwich | 15 cm | 97 kg | 850 kg | 38 kWh |
| foam walls in a glass-epoxy skin, a sandwich | 20 cm | 130 kg | 915 kg | 43 kWh |

## Range

Crewed, sized for each range; and the crewed airframe (sized for 50 km) flying cargo at each range, the battery it doesn't need going to cargo.

| Range | Crewed: max weight | Battery | Cargo on the crewed airframe |
|---|---|---|---|
| 25 km | 814 kg | 27 kWh | 297 kg |
| 50 km | 888 kg | 41 kWh | 246 kg |
| 75 km | 978 kg | 57 kWh | 195 kg |
| 100 km | 1091 kg | 78 kWh | 144 kg |

## Afloat: the feet and the wings

The found layout with each kind of foot, its wing panels buoyant (foam-cored) or free-flooding.

| Feet (radius x length) | Wings | Max weight | Waterline | Feet carry | GM | Rights itself | Least GZ |
|---|---|---|---|---|---|---|---|
| legs with pads | buoyant | 888 kg | 0.96 m | 0 % | 5.9 m | yes | +4 cm |
| legs with pads | flooding | 888 kg | 1.05 m | 0 % | -0.5 m | no: past 10° (0° round) | -39 cm |
| 15 x 80 cm | buoyant | 903 kg | 0.88 m | 16 % | 4.5 m | no: past 80° (60° round) | -4 cm |
| 15 x 80 cm | flooding | 903 kg | 0.97 m | 16 % | -0.7 m | no: past 10° (30° round) | -35 cm |
| 20 x 100 cm | buoyant | 928 kg | 0.78 m | 33 % | 4.2 m | no: past 80° (60° round) | -11 cm |
| 20 x 100 cm | flooding | 928 kg | 0.81 m | 34 % | -0.0 m | no: past 30° (30° round) | -29 cm |
| 25 x 160 cm | buoyant | 983 kg | 0.71 m | 44 % | 5.0 m | no: past 80° (60° round) | -61 cm |
| 25 x 160 cm | flooding | 983 kg | 0.73 m | 45 % | 2.1 m | no: past 60° (60° round) | -12 cm |

## The wing's size

Tip extension is how far the panel runs past the motor pod, in prop radii.

| Tip extension | Chord | Max weight | Cruise | Stall | Props' plane | GM | Rights itself | Least GZ |
|---|---|---|---|---|---|---|---|---|
| 0.6 | 0.8 m | 903 kg | 79 kW at 53 m/s | 42 m/s | 1.67 m | 4.0 m | no: past 60° (30° round) | -2 cm |
| 0.6 | 1.0 m | 919 kg | 72 kW at 48 m/s | 38 m/s | 1.70 m | 5.0 m | no: past 80° (60° round) | -1 cm |
| 0.9 | 0.8 m | 888 kg | 65 kW at 49 m/s | 39 m/s | 1.70 m | 5.9 m | yes | +4 cm |
| 0.9 | 1.0 m | 912 kg | 59 kW at 44 m/s | 35 m/s | 1.72 m | 7.6 m | no: past 90° (60° round) | -8 cm |

## Crouching

The container's centre above the core's floor: the person crouched low, or sitting up.

| Container | CG | Props' plane | GM | Rights itself | Least GZ |
|---|---|---|---|---|---|
| 0.50 m | 1.38 m | 1.70 m | 5.9 m | yes | +4 cm |
| 0.90 m | 1.51 m | 1.83 m | 4.4 m | no: past 60° (30° round) | -4 cm |

## How the hull is built

Each build on the found layout. The envelope is sealed, so it floats whatever its walls are; the walls' foam only matters if it is holed. *Holed* is how many times over the foam alone (the walls', the flotation blocks', the wing panels') floats it, everything else's displacement left out. The structure's stiffness and strength aren't checked: the walls are a weight per square metre.

| Hull | Core walls weigh | Inside | Max weight | Hover | Battery | Core's floor above the water | Holed | GM | Rights itself | Least GZ |
|---|---|---|---|---|---|---|---|---|---|---|
| HDPE-wrapped foam, 18 cm | 176 kg | 1.22 x 2.44 m | 987 kg | 135 kW | 47 kWh | -2 cm | 3.8x | 5.6 m | yes | +0 cm |
| Glass over foam, 18 cm (found) | 116 kg | 1.22 x 2.44 m | 888 kg | 115 kW | 41 kWh | +4 cm | 4.2x | 5.9 m | yes | +4 cm |
| HDPE lattice, foam-filled, 18 cm | 249 kg | 1.22 x 2.44 m | 1109 kg | 161 kW | 54 kWh | -7 cm | 3.2x | 5.2 m | no: past 60° (30° round) | -3 cm |
| HDPE lattice, foam-filled, 10 cm | 146 kg | 1.22 x 2.44 m | 918 kg | 121 kW | 41 kWh | +2 cm | 2.4x | 5.7 m | no: past 70° (30° round) | -4 cm |
| Glass/foam sandwich 25 mm, the outside shrunk to it | 46 kg + 32 kg of blocks | 1.22 x 2.44 m | 797 kg | 98 kW | 32 kWh | +16 cm | 2.8x | 6.4 m | no: past 80° (60° round) | -4 cm |
| Glass/foam sandwich 25 mm, moldless, the same outside | 66 kg + 32 kg of blocks | 1.53 x 2.75 m | 857 kg | 109 kW | 39 kWh | +12 cm | 2.7x | 6.9 m | yes | +9 cm |
| Carbon/foam sandwich 25 mm, molded, the same outside | 52 kg + 32 kg of blocks | 1.53 x 2.75 m | 834 kg | 105 kW | 38 kWh | +14 cm | 2.8x | 7.1 m | yes | +9 cm |
