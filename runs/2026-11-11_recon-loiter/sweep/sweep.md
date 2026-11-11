# The loiter craft: hours on station

Speed is not the problem; time to observe is. The job: watch the boat's surroundings on passage, circling it at 2 km, for hours (2 km out, 120 m up, watching for a skiff; the boat sails on at 6.5 kn in 15 kn of wind, ss3). Each airframe is sized (OpenMDAO + OpenAeroStruct) for each time on station and battery, flown through it in the 3-DOF sim, and floated (`recon/loiter.py`). Both are moulded, carry the same gimbal, avionics and long-range link, and stow in panels to at most 4 m of span; a battery of at most 10 kg keeps the craft one or two people can handle from a boat.

- **Lifting body** (`--airframe liftbody`): a blended wing body, the battery inside its thick centre body, one pusher; it takes off from the water on a planing shoe and lands on it.
- **Tandem tilt-wing** (`--airframe tiltwing`): two high wings, the rear 1.2 m aft on a pylon 30 cm up, that turn up to hover; a prop a side on each, and nacelles whose tails behind the wing are floats. On the water it rests on its V-keel hull with the wings turned 55° up, the front float tails dipped in either side as outriggers; it lifts straight off and turns the wings forward to fly.

## Take-off mass for each time on station

| Hours on station | lifting body, 200 Wh/kg | lifting body, 300 Wh/kg | tandem tilt-wing, 200 Wh/kg | tandem tilt-wing, 300 Wh/kg |
|---|---|---|---|---|
| 2 h | 3.3 kg, 2.6 m | 2.8 kg, 2.1 m | 4.2 kg, 2.0 + 2.0 m | 3.7 kg, 2.0 + 2.0 m |
| 4 h | 5.2 kg, 4.0 m | 3.9 kg, 3.2 m | 6.6 kg, 3.0 + 3.5 m | 4.7 kg, 2.0 + 3.0 m |
| 6 h | 8.6 kg, 4.0 m | 5.1 kg, 4.0 m | 14.3 kg, 4.0 + 3.7 m | 6.3 kg, 3.0 + 3.5 m |
| 8 h | doesn't close | 6.8 kg, 4.0 m | doesn't close | 9.1 kg, 4.0 + 3.7 m |
| 10 h | doesn't close | 11.3 kg, 4.0 m | doesn't close | doesn't close |
| 12 h | solver didn't settle | doesn't close | doesn't close | doesn't close |

"Doesn't close": no design meets every constraint with the battery inside its bounds. "Solver didn't settle": OpenAeroStruct's coupled wing-and-spar solve failed from every start, so the case is unknown, not infeasible.

## Each design, 200 Wh/kg

| | Mass | Battery | Spans | L/D | Loiter | Back aboard | Launch and recovery | Afloat |
|---|---|---|---|---|---|---|---|---|
| lifting body, 2 h | 3.3 kg | 1.0 kg (31 %) | 2.6 m | 14.4 | 13.3 m/s, 66 W | 17 % left | off the water, waves to 5 cm (ss0): 11 m run; lands at 4.2 g | 5.8x reserve, trim +1°, props 19 cm in the water |
| lifting body, 4 h | 5.2 kg | 2.3 kg (43 %) | 4.0 m | 18.8 | 12.1 m/s, 71 W | 17 % left | off the water, waves to 5 cm (ss0): 11 m run; lands at 3.0 g | 7.7x reserve, trim -1°, props 18 cm in the water |
| lifting body, 6 h | 8.6 kg | 4.9 kg (57 %) | 4.0 m | 19.7 | 12.4 m/s, 104 W | 17 % left | off the water, waves to 5 cm (ss0): 14 m run; lands at 2.6 g | 9.9x reserve, trim -3°, props 18 cm in the water |
| tandem tilt-wing, 2 h | 4.2 kg | 1.3 kg (32 %) | 2.0 + 2.0 m | 13.7 | 12.6 m/s, 84 W | 13 % left | lifts off on its props: 292 W to hover, 6 Wh a sortie | 20.5x reserve, trim +1°, on its keel and front float tails, props 16 cm clear, the gimbal 14 cm clear |
| tandem tilt-wing, 4 h | 6.6 kg | 2.8 kg (43 %) | 3.0 + 3.5 m | 19.4 | 11.5 m/s, 85 W | 17 % left | lifts off on its props: 583 W to hover, 11 Wh a sortie | 15.2x reserve, trim +2°, on its keel and front float tails, props 16 cm clear, the gimbal 14 cm clear |
| tandem tilt-wing, 6 h | 14.3 kg | 8.9 kg (62 %) | 4.0 + 3.7 m | 19.6 | 13.2 m/s, 184 W | 17 % left | lifts off on its props: 1837 W to hover, 36 Wh a sortie | 9.9x reserve, trim +1°, on its keel and front float tails, props 14 cm clear, the gimbal 11 cm clear |

## Each design, 300 Wh/kg

| | Mass | Battery | Spans | L/D | Loiter | Back aboard | Launch and recovery | Afloat |
|---|---|---|---|---|---|---|---|---|
| lifting body, 2 h | 2.8 kg | 0.7 kg (25 %) | 2.1 m | 12.6 | 13.9 m/s, 67 W | 17 % left | off the water, waves to 5 cm (ss0): 12 m run; lands at 4.8 g | 5.3x reserve, trim +1°, props 20 cm in the water |
| lifting body, 4 h | 3.9 kg | 1.4 kg (35 %) | 3.2 m | 16.4 | 12.6 m/s, 65 W | 17 % left | off the water, waves to 5 cm (ss0): 11 m run; lands at 3.6 g | 6.7x reserve, trim +0°, props 19 cm in the water |
| lifting body, 6 h | 5.1 kg | 2.2 kg (43 %) | 4.0 m | 18.8 | 12.0 m/s, 70 W | 17 % left | off the water, waves to 5 cm (ss0): 11 m run; lands at 3.0 g | 7.9x reserve, trim -1°, props 18 cm in the water |
| lifting body, 8 h | 6.8 kg | 3.5 kg (51 %) | 4.0 m | 19.7 | 12.0 m/s, 85 W | 17 % left | off the water, waves to 5 cm (ss0): 12 m run; lands at 2.7 g | 9.3x reserve, trim -2°, props 19 cm in the water |
| lifting body, 10 h | 11.3 kg | 7.2 kg (64 %) | 4.0 m | 19.4 | 12.9 m/s, 140 W | 17 % left | off the water, waves to 5 cm (ss0): 17 m run; lands at 2.6 g | 10.7x reserve, trim -4°, props 17 cm in the water |
| tandem tilt-wing, 2 h | 3.7 kg | 0.8 kg (23 %) | 2.0 + 2.0 m | 13.3 | 12.5 m/s, 76 W | 16 % left | lifts off on its props: 240 W to hover, 5 Wh a sortie | 23.5x reserve, trim +1°, on its keel and front float tails, props 17 cm clear, the gimbal 15 cm clear |
| tandem tilt-wing, 4 h | 4.7 kg | 1.5 kg (32 %) | 2.0 + 3.0 m | 16.8 | 11.4 m/s, 72 W | 18 % left | lifts off on its props: 349 W to hover, 7 Wh a sortie | 19.5x reserve, trim +4°, on its keel and front float tails, props 22 cm clear, the gimbal 19 cm clear |
| tandem tilt-wing, 6 h | 6.3 kg | 2.6 kg (41 %) | 3.0 + 3.5 m | 19.0 | 11.5 m/s, 83 W | 17 % left | lifts off on its props: 540 W to hover, 11 Wh a sortie | 15.5x reserve, trim +1°, on its keel and front float tails, props 16 cm clear, the gimbal 13 cm clear |
| tandem tilt-wing, 8 h | 9.1 kg | 4.6 kg (51 %) | 4.0 + 3.7 m | 19.7 | 11.8 m/s, 111 W | 17 % left | lifts off on its props: 928 W to hover, 18 Wh a sortie | 12.4x reserve, trim +1°, on its keel and front float tails, props 16 cm clear, the gimbal 13 cm clear |

