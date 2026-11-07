# Osprey Recon: landing on the sea and taking off from it

**Status: work in progress.** This is the design notebook for Recon's water operations, kept here until
the design settles. The main [README](../../README.md) carries only a pointer, and the Recon models are
described in [docs/recon.md](../recon.md). Every input is a REF stand-in, so the numbers show which way
the design should move, not what to build.

![The twin-boom, the blended wing and the crescent afloat at the draft and trim the model finds, each prop raised on the pylon it needs](../img/recon-afloat.png)

## Why the bird needs to float

Recon is recovered to a moving boat. Sometimes it won't make the boat: the sea is too rough for a hand or
net catch, the battery is low, or something has failed. Then it should come down on the water nearby,
float and wait for a boathook. And in a quiet anchorage, a bird that takes off from the water can be
launched off the swim platform, with no catapult and no throw.

## What water asks of the bird

The spec, in `[water]` of [`design/recon/airframe.toml`](../../design/recon/airframe.toml), with an overlay
per airframe:

| Requirement | Spec (REF) | Why |
|---|---|---|
| Reserve buoyancy | Sealed volume at least 2 × what it displaces | Floats with half its volume dry; seaplane floats carry 1.8 |
| Floating trim | About level | Nose high or tail low puts the prop or the elevons in the water and makes the take-off run start badly |
| Prop clear of the water | Tips 5 cm above the calm waterline, afloat | Spray in the first metres of the run eats a prop, and a pusher sits in the worst of it |
| Cameras clear of the water | Out of it, afloat | Salt on a lens, and a gimbal under the belly is the first thing to hit |
| Getting over the hump | Thrust, less air drag and water resistance, at least 0.10 × weight all the way | Water resistance peaks at the hump before the hull climbs onto its step and planes; a hull that can't get over it never gets off |
| Waves for take-off | Significant height up to 10 % of the planing shoe's length | A rule of thumb from floatplanes |
| Landing loads | FAR 23.527 hull load factor, against the 3 g the structure is sized for | Touching down on water is a slam, and it grows with the square of the touchdown speed |
| The float kit | 0.10–0.14 kg: a planing shoe with a step and a 20° V bottom, seals and gaskets, a prop pylon; 0.0015 m² of drag area | Sized and flown with the bird |

## How the model works

[`src/osprey/recon/water.py`](../../src/osprey/recon/water.py), run with `osprey recon-water`:

- **Afloat:** it floats the sized bird's own meshes (the ones the renders draw: wing, pod, booms, tail). The
  volume below the waterline comes from the divergence theorem over the clipped surface. It solves for the
  draft that displaces the bird's weight and the trim that puts the centre of buoyancy under the CG, then
  measures the prop's and the cameras' clearance.
- **Take-off:** a run on calm water at full power. Static thrust is momentum theory with a figure of merit
  (18 N from the REF 400 W motor and 23 cm prop), falling off with speed. Water resistance is a hump curve
  on the weight still on the water, and air drag uses the sized polar. Lift-off is at 1.15 × stall.
- **Landing:** the FAR 23.527 hull load factor from stall speed, weight and the shoe's deadrise.
- **Mass:** every job is flown again with the kit. `--water` sizes the bird with the kit aboard from the
  start, like any other fixed mass.

```bash
uv run osprey recon-water --run runs/2026-11-06_recon-wings/bwb/gimbal --mission sar-offshore --airframe bwb
uv run osprey recon --mission all --airframe bwb --water      # size and fly all seven jobs with the kit aboard
uv run osprey recon-water --mission sar-offshore --airframe bwb --water
```

## Results: the float plane

Each airframe's do-everything bird, with each payload, from
[`runs/2026-11-07_recon-water`](../../runs/2026-11-07_recon-water/). `bolt-on/` takes the birds sized
without the kit and adds it. `sized/` sizes and flies all seven jobs again with the kit aboard from the
start, and the same jobs set the one-bird as before.

| Bird | Without the kit | Kit bolted on | Sized with the kit | Reserve buoyancy | Trim afloat | Prop pylon | Take-off run | Landing load |
|---|---|---|---|---|---|---|---|---|
| Twin-boom, gimbal | 2.73 kg | 2.85 kg, eats the reserve | **3.01 kg** | 2.5 | level | 18 cm | 18 m | 6.3 g |
| Twin-boom, side eyes | 2.13 kg | 2.25 kg, eats the reserve | **2.33 kg** | 2.7 | level | 18 cm | 15 m | 7.4 g |
| Blended wing, gimbal | 2.11 kg | 2.21 kg, eats the reserve | **2.38 kg** | 2.9 | level | 17 cm | 15 m | 7.4 g |
| Blended wing, side eyes | 1.80 kg | 1.90 kg, eats the reserve | **1.97 kg** | 2.9 | level | 17 cm | 12 m | 7.9 g |
| Crescent, gimbal | 2.18 kg | 2.32 kg, eats the reserve | **2.51 kg** | **1.6** | **12° nose up** | 19 cm | 16 m | 7.2 g |
| Crescent, side eyes | 1.83 kg | 1.97 kg, eats the reserve | **2.05 kg** | **1.7** | **16° nose up** | 24 cm | 13 m | 7.7 g |

<sub>Reserve buoyancy is sealed volume over volume displaced (spec ≥ 2). The pylon is what lifts the prop
tips 5 cm clear of the calm water, afloat. The run is on calm water at full power. The landing load is
FAR 23.527 with a 20° V shoe; the structure is sized for 3 g. "Eats the reserve": the hardest job lands
with 2–9 % of the battery left, against the 17 % the missions keep. Each bird's full sheet is
`water/water.md` in its directory.</sub>

What it says:
- **Floating is the easy part, except for the crescent.** The twin-boom and the blended wing float level
  on their wings with 2.5–2.9 × the volume they need. The crescent's slim pod is forward and its mass is
  aft, so it floats 12–16° nose up with its swept wings awash, at 1.6–1.7 ×. It needs more sealed volume
  aft: foam-filled panels, or sponsons at the wing roots.
- **Every pusher prop sits 12–18 cm under the water.** Each layout needs its prop raised 17–24 cm on a
  pylon, or a different arrangement: a tractor prop on the nose, or two motors on top of the wing. This is
  the biggest change to the layouts, and a high thrust line pitches the nose down, which the elevons
  would have to hold.
- **The cameras are in the water.** The belly gimbal sits 3–12 cm under it, and so do the side eyes. They
  need to retract, or move up.
- **Getting off is not the problem.** The REF 400 W motor and 23 cm prop give 18 N of static thrust (T/W
  0.6–1.0). That clears the hump with 0.4–0.8 × the weight to spare, against the 0.1 asked, in a 12–18 m
  run of about 2 s using 0.3 Wh.
- **The sea is the problem.** A planing shoe 42–50 cm long takes off in waves of 4–5 cm at most: a
  marina, a glassy anchorage, or a slick in the boat's lee. In the sea states Recon works in (sea state
  3–4, 0.9–1.9 m), take-off from the water is out. Launch from the deck and come down on the water.
- **Landing on the water is a slam.** At 6–8 g, landing loads are two to three times what the structure is
  sized for. A sharper V helps (a 30° shoe takes about a quarter off), so does a slower touchdown, and so
  does a parachute.
- **The kit costs twice its weight.** The 0.10–0.14 kg kit, bolted onto birds sized without it, eats the
  energy reserve on their hardest job. Sized in from the start, it adds 0.17–0.33 kg: a bigger wing and
  battery to carry it. The blended wing with side eyes stays lightest, at 1.97 kg.

## Prior art: the WingtraRAY

The [WingtraRAY](https://wingtra.com/ray/) is a commercial survey drone of about Recon's class that takes
the other road. It never touches the water.

| | WingtraRAY | Recon blended wing (gimbal, today) |
|---|---|---|
| Layout | Tailsitter VTOL flying wing: takes off and lands standing on its tail, flies as a wing | Tailless flying wing, thrown or catapulted, caught in a net or by hand |
| Span | 125 cm (125 × 68 × 12 cm without the landing fin) | 132 cm |
| Take-off mass | 5.2 kg, 1.25 kg of payload | 2.1 kg |
| Battery | Two 99 Wh packs, either one enough to get home | 0.88 kg of Li-ion, about 175 Wh |
| Flight time, speed | 59 min (RGB), 16–22 m/s | About 2 h at 17 m/s |
| Weather | 12 m/s sustained wind; IP53, not for rain, fog or snow | Not rated |
| Water | Nothing claimed; IP53 is splash-proof, not floating | Floats; this notebook |
| Safety | Optional parachute, automatic or manual | None |

<sub>Numbers from Wingtra's product page and vendor listings
([volatusdrones.ca](https://volatusdrones.ca/products/wingtraray),
[geo-matching.com](https://geo-matching.com/products/wingtraray)); Recon's from
[`runs/2026-11-06_recon-wings`](../../runs/2026-11-06_recon-wings/).</sub>

What it says for Recon:
- **Vertical take-off and landing removes the problem this notebook is trying to solve.** A tailsitter
  launches and lands on a few square metres of deck: no catapult, no net, and no water take-off. Floating
  then becomes only the ditching case.
- **It costs mass and endurance.** The Ray weighs two and a half times what Recon does, and flies half as
  long on a little more battery. Hover power sets its motors, and the transitions spend energy.
- **A boat's deck moves.** The Ray lands on ground. Landing a tailsitter on a pitching, rolling stern in
  sea state 3–4, with apparent wind, is the hard part, and Osprey already models the boat's motion (Nest).
- **Two batteries, each under 100 Wh**, give redundancy, and packs under 100 Wh fly as airline carry-on:
  that matters to a cruising boat.
- **A parachute is a third option.** It lowers a fixed wing onto the water at a few metres per second,
  straight down. There's no planing slam, so the 7–8 g landing load goes, and so do the shoe and the step.
  The bird still has to float, seal and keep its prop and cameras safe, but it no longer takes off from
  the water.

So there are three ways to go:

| | Float plane (this notebook) | Fixed wing + parachute to the water | Tailsitter VTOL (Wingtra's way) |
|---|---|---|---|
| Launch | From the water in flat calm; from the deck otherwise | From the deck (throw or catapult) | From the deck, vertically |
| Recovery | Planing landing on the water, then the boathook | Parachute onto the water, then the boathook | Vertically onto the deck |
| What it adds | Shoe and step, prop pylon, 7–8 g structure, seals | Parachute and its bay, seals, floating volume | Hover motors and battery, deck-landing control |
| Limit | Waves of a few cm for take-off | Wind drift under the canopy; finding it in the water | Deck motion and gusts on landing |

## Not worked out yet

- **The hydrodynamics are REF.** The hump and planing resistance, the hump speed, the take-off attitude
  and the wave rule are stand-ins from floatplane practice. Tank data for a small shoe would replace them.
- **Calm water only.** Waves, spray, porpoising and weathercocking afloat aren't modelled.
- **Upright only.** It isn't checked whether a bird turned over on landing rights itself, or floats
  inverted.
- **The pylon's pitching moment** and the elevon trim it costs aren't in the sizing.
- **The meshes overlap.** Where the wing passes through the pod, the volume counts twice, so reserve
  buoyancy is a little high on the twin-boom and the crescent.
- **Salt.** Sealing and the motor's tolerance of a dunking are mass in the kit, not a design.
