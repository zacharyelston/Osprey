# The sailplane: a soaring relay with a truss-braced wing

**Status: work in progress.** A thermal-soaring sailplane that loiters for hours as an airborne radio relay
and spectrum scanner: a laminar body of revolution and a thin, high-aspect-ratio wing in three pieces with
swappable outer panels (solar by day, light by night). The wing is braced as NASA's transonic truss-braced
wing is: one brace a side from low on the body up to the wing, and a jury strut from each brace up to the wing.

It arrived as an engineering handoff package. Its numbers are in
[`design/recon/sailplane.toml`](../../design/recon/sailplane.toml); where the package was silent the value is a
REF stand-in. Three designs come out of it:

| | |
|---|---|
| ![The pusher: a thin braced wing on a round body](../img/recon-sailplane-assembly.png) | **Pusher**: the package's own body, tail and 4.8 m span, kept as the record of what was handed over. One prop in the tail cone. |
| ![The twin: push-pull pods on the wing, a V-tail on a longer body](../img/recon-sailplane-twin.png) | **Twin** ([`twin.toml`](../../design/recon/sailplanes/twin.toml)): a push-pull pod on each wing where the brace meets it, an upright V-tail, a 6.0 m wing and a 2.3 m body. |
| ![The boom: tractor props on the pods, booms aft to a tailplane and two fins](../img/recon-sailplane-boom.png) | **Boom** ([`boom.toml`](../../design/recon/sailplanes/boom.toml)): the tail on twin booms from the wing's pods, a short body hung from the wing with a pusher at its back, a tractor on each pod, the same 6.0 m wing. |

```
uv run osprey recon-sailplane                      # the pusher; out/recon-sailplane/pusher
uv run osprey recon-sailplane --variant twin       # or boom
uv run osprey recon-sailplane --variant twin --pods front    # the twin's props at the front, back or both
```

Each writes `sailplane.md`, `cutlist.csv`, `wing.png` and `scad/`, and exits 1 while any finding fails. The
pusher fails three, all in the package's own numbers. The twin and the boom fail none.

| | Span, m | All-up, kg | Motors | Tail, m² | Tail volumes | L/D | Sink, m/s | Stall, m/s | Under power, h | One motor out | Fails |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pusher (the package) | 4.8 | 18.0 | 1 | 0.22 | 0.18, 0.009 | 25.9 | 0.56 | 11.8 | 5.6 | no thrust | 3 |
| twin | 6 | 21.3 | 4 | 0.31 | 0.40, 0.020 | 28.5 | 0.51 | 11.5 | 5.2 | 2.1 m/s, tail CL 0.62 | none |
| boom | 6 | 19.5 | 3 | 0.44 | 0.40, 0.020 | 28.4 | 0.51 | 11.0 | 5.9 | 1.8 m/s, tail CL 0.41 | none |

The pusher's glide is with a tail less than half the size it needs. A variant's all-up weight is worked out:
the package's 18.0 kg plus what its propulsion, tail, booms, body skin and longer panels add.

## What was wrong, and what was done

| Flaw | Where | Fix |
|---|---|---|
| A "Warren space-frame truss" inside the wing: 56 mm deep in a 35 mm section, and its chords buckled at 4 g | the package | A misreading of *truss-braced wing*. One spar inside the section, and braces outside it |
| Tail volumes of 0.18 and 0.009 against 0.40 and 0.020 | the package: 0.22 m² of tail 0.74 m behind the wing | The twin's body is stretched and its V-tail sized, and angled, to just meet both; the boom's tail is sized the same way |
| The tail cone is at 7 mm radius at the firewall, not the spinner's 22: a 62 mm parallel stinger | the package | The boom's body is cut at x = 1352, where the cubic meets the spinner. The twin has no spinner there |
| 72 cells are 1,296 Wh, not the quoted 488 | the package | The pack is right and the figure was wrong: holding height under power takes about 200 W, so 4 h needs the 72 cells. The variants quote what the cells hold |
| The sink quoted, 0.52 m/s, is what a wing with no braces and an undersized tail gives | the package | Induced drag is most of the sink. The wing is stretched to 6.0 m: 0.51 m/s with braces, pods and a full-sized tail |
| One of two motors out: the tail cannot hold the yaw | the twin with props at the front or back only | A prop at both ends of each pod: one of four out leaves 75 % of the thrust and half the yaw |
| Brace pins at 57 to 63 MPa of bearing in a printed tang, against 60 | all three | 6 mm pins through 7 mm tangs: 41 MPa on the twin and 46 on the boom, with the solved lift |
| A 30 mm spar at 7 % of its strength, 645 g | my first sizing | A 27.3 x 25.3 mm tube and 1 mm joiners: 541 g of carbon in the pusher's wing, was 1,006 |
| A 90 mm brace fairing, a quarter of the wing's own profile drag | my first sizing | 68 mm at 20 % thick, as slim as the 12 mm tube allows |
| The boom's tail load twists the wing, unchecked | the boom | Checked: 0.66° in the skin box between body and boom, against 1° allowed |
| All-up weights set by hand | the variants | Worked out from what each variant adds; a motor's weight follows the climb's power |

## The science

Ting, Reynolds, Nguyen and Totah, *Aerodynamic Analysis of the Truss-Braced Wing Aircraft Using
Vortex-Lattice Superposition Approach* (AIAA), on the Boeing SUGAR truss-braced wing. Three things are taken
from it:

- The wing is braced "at approximately mid-span" with one jury strut a side. So are the pusher and the twin.
- The braces are lifting surfaces. In their component build-up the braces carry 8.5 % of the lift and about
  8 % of the drag. Here the braces carry that share of the lift in the load cases, and their fairing is an
  aerofoil, not a streamlined tube.
- Their drag build-up (their Eqs. 1–4): each component's skin friction with transition, times a form factor,
  times its wetted area, plus induced drag. It leaves out interference where the parts meet, as theirs does.

Their superposition method is used too, on a vortex lattice: see below.

## The lift, solved

`src/osprey/recon/sailplane_vlm.py` solves the lift with a vortex lattice (OpenAeroStruct, which the other
Recon airframes are already sized with): camber sheets for the wing, the braces and the tail. It is solved two
ways, as the paper does. All together, each surface in the others' wash; and each surface alone with the
forces added, their superposition method 2, which they found close to CFD where the whole lattice was not. The
loads take the second (`[aero] lift = "vlm"`; `"elliptic"` is the old assumption). For the twin, at the
loiter's lift:

| | Lift-curve slope, /rad | Lift at zero angle | Angle, deg | Wing's share | Braces' share | Tail, untrimmed | Span efficiency |
|---|---|---|---|---|---|---|---|
| each surface alone, summed | 6.08 | 0.26 | 5.3 | 92.4% | 7.6% | +5.1% | n/a |
| all in one lattice | 5.72 | 0.26 | 5.7 | 93.8% | 6.2% | +3.5% | 1.00 |
| no braces | 5.52 | 0.25 | 5.9 | 100.0% | 0.0% | +5.7% | 0.99 |

- **The braces carry 7.6%** by components and 6.2% all together, against the paper's 8.5 % for the
  SUGAR wing. The boom's short braces carry 3.5%.
- **The lift sits further out than an ellipse**: centred 1.34 m along the wing in the pull-up, not 1.27. A
  constant-chord centre section and moderate taper do that. So the wing is loaded harder than was assumed: on
  the twin each brace pulls 1075 N, not 959, and is at 0.71 of its buckling load, not 0.65. On the boom the
  pull went from 1,047 to 1227 N, which put its pins over; they are now 6 mm in 7 mm tangs.
- **Span efficiency is 1.00** for the lattice, with no body and nothing viscous. The drag build-up keeps its
  0.90.

![The twin's lift along one wing in the pull-up: the lattice's against an ellipse of the same lift](../img/recon-sailplane-lift.png)

The lattice has no body, pods or booms, no thickness and no stall, and its tail is at zero incidence, not
trimmed. The brace-station and pod sweeps still use the elliptic lift.

## The wing and its braces

One spar inside the SD7037 at 30 % chord, a square carbon tube whose bore takes the outer panels' 25 mm
joiners. A brace a side, a 12 mm tube in an aerofoil fairing, from a pin outside the hull on the front main
bulkhead to a pin under the wing. A jury strut from the middle of each brace up to the spar halves the brace's
buckling length.

![From the front: the wing, the two braces and their jury struts](../img/recon-sailplane-front.png)

The loads are a +4 g pull-up and a -2 g push-over at a 1.5 ultimate factor, day and night wings, on a frame
of beam elements pinned to the body at the wing's saddle and at the braces' roots, under the lattice's lift.

| | Spar bending with no braces, N m | with braces | Tip's rise with no braces, mm | with braces | Each brace pulls, N |
|---|---|---|---|---|---|
| pusher, braces at mid-span | 246 | 46 | 262 | 24 | 801 |
| twin, braces at mid-span | 332 | 66 | 544 | 54 | 1075 |
| boom, braces at the panels' joint | 315 | 157 | 514 | 170 | 1227 |

Where the braces meet the wing, on the pusher:

![The wing from the front with each tube coloured by how much of its strength is used, and the effect of the brace's station](../img/recon-sailplane-wing.png)

| Brace at y, mm | Spar bending, N m | at the root, N m | Tip in the pull-up, mm | Brace tension, N | Brace compression in the push-over, N | Spar compression, N | Brace used | Most used |
|---|---|---|---|---|---|---|---|---|
| no braces | 228 | 228 | 234 | 0 | -0 | 0 | 0.00 | 0.77 |
| 500 | 124 | 46 | 88 | 940 | 470 | 783 | 0.13 | 0.38 |
| 650 | 100 | 43 | 65 | 858 | 429 | 773 | 0.11 | 0.30 |
| 800 | 79 | 41 | 47 | 806 | 403 | 754 | 0.15 | 0.23 |
| 1000 | 55 | 39 | 30 | 762 | 381 | 732 | 0.22 | 0.22 |
| 1200 | 40 | 40 | 18 | 726 | 363 | 704 | 0.31 | 0.31 |
| 1400 | 43 | 43 | 10 | 700 | 350 | 682 | 0.41 | 0.41 |

At mid-span the brace's wing pin is on the outer panel, so swapping a panel means pulling it. At the joint
(800) the panels swap freely, for about twice the bending.

## The twin

![The twin from the front](../img/recon-sailplane-twin-front.png)

- **Wing.** 6.0 m: the outer panels are 2.2 m each, not 1.6. Sink falls from 0.58 to 0.51 m/s and the
  stall from 12.2 to 11.5 m/s. The brace is at 0.71 of its buckling load in the push-over, the
  most-used tube.
- **Body.** 2.3 m. With the tail sized at each length, the best for this wing is 2.4 m and the curve is
  flat; 2.3 m is 0.7 kg lighter than 2.6. The cubic tail cone can be drawn out to 3.07 m before it swells
  past the body's radius.
- **Tail.** A V of 0.31 m² at 43.7° from the horizontal: the angle at which one area meets both volumes.
- **Weight.** 21.3 kg. That is 3.3 kg over the package's 18: longer panels, more body skin, a bigger tail
  and four motors.
- **Balance.** The battery slides 39 mm aft of where the package has it, of 160 mm either way.

### Where the props go on the pods

| | | |
|---|---|---|
| ![Front: a tractor prop ahead of the leading edge](../img/recon-sailplane-pods-front.png) | ![Back: a pusher behind the trailing edge](../img/recon-sailplane-pods-back.png) | ![Both: a pod the length of the chord with a prop at each end](../img/recon-sailplane-pods-both.png) |
| front | back | both |

| Props | Motors | Pod, mm | Pod, kg | All-up, kg | Battery slides aft, mm | Pods, counts | L/D | Sink, m/s | Props' efficiency | Shaft a motor, W | One out: thrust left | climb, m/s | yaw, N m | tail CL | Brace pull at 4 g, N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| front | 2 | 200 | 0.33 | 20.8 | 72 of 160 | 1.8 | 28.6 | 0.507 | 55% | 644 | 50% | 1.2 | 37 | 1.21 **over** | 966 |
| back | 2 | 200 | 0.33 | 20.8 | 17 of 160 | 1.8 | 28.6 | 0.507 | 55% | 650 | 50% | 1.2 | 37 | 1.21 **over** | 966 |
| both | 4 | 535 | 0.58 | 21.3 | 39 of 160 | 3.3 | 28.5 | 0.508 | 52% | 350 | 75% | 2.1 | 19 | 0.62 | 959 |

- **Front and back fail with one motor out.** Half the thrust is gone, 1.5 m off the centre line, and the
  V-tail is asked for a lift coefficient of 1.21. It has about 0.9.
- **Both holds**, at 0.62, with 2.1 m/s of climb left. It costs 0.5 kg and almost nothing in sink.
- **Front against back is a draw** but for the balance: a back prop's weight is further aft.

### How long the body can be

| Length, m | Fineness | Tail arm, m | Tail, m^2 | Volumes, horizontal and vertical | Body skin, m^2 | Body, counts | Tail, counts | All-up, kg | Tail cone's steepest, deg | L/D | Sink, m/s | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.3 | 7.7 | 1.59 | 0.31 | 0.40, 0.020 | 1.59 | 23 | 19 | 21.3 | 10.9 | 28.5 | 0.508 | as designed |
| 1.45 | 4.8 | 0.74 | 0.67 | 0.40, 0.020 | 1.00 | 14 | 41 | 20.0 | 16.0 | 27.1 | 0.536 |  |
| 1.6 | 5.3 | 0.89 | 0.56 | 0.40, 0.020 | 1.10 | 15 | 34 | 20.1 | 13.3 | 27.6 | 0.525 |  |
| 1.8 | 6.0 | 1.09 | 0.45 | 0.40, 0.020 | 1.23 | 17 | 28 | 20.4 | 11.3 | 28.1 | 0.517 |  |
| 2 | 6.7 | 1.29 | 0.38 | 0.40, 0.020 | 1.37 | 20 | 23 | 20.7 | 11.0 | 28.3 | 0.512 |  |
| 2.2 | 7.3 | 1.49 | 0.33 | 0.40, 0.020 | 1.52 | 22 | 20 | 21.1 | 10.9 | 28.5 | 0.509 |  |
| 2.3 | 7.7 | 1.59 | 0.31 | 0.40, 0.020 | 1.59 | 23 | 19 | 21.3 | 10.9 | 28.5 | 0.508 |  |
| 2.4 | 8.0 | 1.69 | 0.29 | 0.40, 0.020 | 1.67 | 24 | 18 | 21.5 | 10.9 | 28.5 | 0.508 |  |
| 2.6 | 8.7 | 1.89 | 0.26 | 0.40, 0.020 | 1.84 | 27 | 16 | 21.9 | 10.9 | 28.5 | 0.508 |  |
| 2.8 | 9.3 | 2.09 | 0.24 | 0.40, 0.020 | 2.01 | 29 | 14 | 22.4 | 10.9 | 28.5 | 0.509 |  |
| 3 | 10.0 | 2.29 | 0.22 | 0.40, 0.020 | 2.19 | 32 | 13 | 22.9 | 10.9 | 28.4 | 0.511 |  |
| 3.2 | 10.7 | 2.49 | 0.20 | 0.40, 0.020 | 2.38 | 35 | 12 | 23.5 | 10.9 | 28.2 | 0.514 | swells |

A short body pays in tail area, a long one in skin and weight. From about 2.0 m the tail cone is never steeper
than its 11° closing angle; at the package's 1.45 m it reaches 16°.

## The boom

| | |
|---|---|
| ![From behind: the pusher's disc at the body's tail, between the booms and ahead of the tailplane](../img/recon-sailplane-boom-rear.png) | ![From the front](../img/recon-sailplane-boom-front.png) |

- **The braces, pods and booms are at the outer panels' joint**, y = ±800. The booms are 1.6 m apart and the
  outer panels swap without touching brace or boom. A tailplane between booms at mid-span would be twice as
  wide and half the chord.
- **The tail sizes itself.** The tailplane spans the booms 250 mm behind the pusher's disc, 144 mm in
  chord; two fins 525 mm tall. Longer booms than the first cut: 0.44 m² of tail, not 0.52.
- **Booms.** Two 25 mm carbon tubes 1241 mm long, 290 g the pair, at 0.27 of their strength under the
  tailplane's most lift, bending 26 mm. The load twists the wing 0.66° at each pod.
- **Three motors.** One pod motor out leaves two thirds of the thrust, 1.8 m/s of climb, and the fins hold
  the yaw at a lift coefficient of 0.41. With the pusher out there is no yaw at all.
- **Weight and balance.** 19.5 kg, 1.8 kg lighter than the twin, on the package's short body. The battery
  sits 5 mm from where the package has it.
- **The wing bends more.** With the braces at the joint of a 6.0 m wing the tip rises 170 mm in the pull-up,
  6 % of the half-span, against the twin's 54.

## How long the wing can be

The outer panels stretched, the tubes as they are. On the twin:

| Span efficiency |
|---|---|---|---|---|---|---|---|
| each surface alone, summed | 6.08 | 0.26 | 5.3 | 92.4% | 7.6% | +5.1% | n/a |
| all in one lattice | 5.72 | 0.26 | 5.7 | 93.8% | 6.2% | +3.5% | 1.00 |
| no braces | 5.52 | 0.25 | 5.9 | 100.0% | 0.0% | +5.7% | 0.99 |

Drag due to lift does not add up surface by surface (each is in the others' wash), so the summed solve gives no span efficiency. The lattice has no body, no thickness and nothing viscous.

## Where the braces meet the wing

| Brace at y, mm | Spar bending, N m | at the root, N m | Tip in the pull-up, mm | Brace tension, N | Brace compression in the push-over, N | Spar compression, N | Brace used | Most used |
|---|---|---|---|---|---|---|---|---|
| no braces | 305 | 305 | 478 | 0 | -0 | 0 | 0.00 | 1.08 |
| 500 | 203 | 70 | 235 | 1367 | 684 | 1141 | 0.20 | 0.74 |
| 650 | 172 | 67 | 188 | 1247 | 624 | 1126 | 0.18 | 0.63 |
| 800 | 144 | 62 | 148 | 1171 | 585 | 1096 | 0.21 | 0.43 |
| 1000 | 112 | 57 | 106 | 1103 | 551 | 1062 | 0.32 | 0.32 |
| 1200 | 84 | 54 | 73 | 1043 | 522 | 1015 | 0.44 | 0.44 |
| 1400 | 60 | 53 | 49 | 986 | 493 | 967 | 0.58 | 0.58 |

## Drag, by components

Skin friction with transition times a form factor times wetted area for each part, plus induced drag, as Ting, Reynolds, Nguyen and Totah build the truss-braced wing's up. Counts are 0.0001 on the wing's 1.97 m^2. The braces' planform is 10% of the wing's.

| Speed, m/s | CL | Wing | Braces | Tail | Body | Pods | Induced | L/D | Sink, m/s | L/D, no braces | Sink, no braces |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 14.5 | 0.82 | 90 | 22 | 19 | 23 | 3 | 131 | 28.5 | 0.51 | 30.9 | 0.47 |
| 16.5 | 0.63 | 86 | 21 | 18 | 22 | 3 | 78 | 27.7 | 0.59 | 30.6 | 0.54 |
| 18.5 | 0.50 | 83 | 20 | 17 | 22 | 3 | 49 | 25.9 | 0.71 | 29.0 | 0.64 |

## Where the props go on the pods

A tractor at the front of each pod, a pusher at the back, or both. The props are sized for a 3 m/s climb at 14.5 m/s; a motor's weight follows its power. Glide is with the props folded.

| Props | Motors | Pod, mm | Pod, kg | All-up, kg | Battery slides aft, mm | Pods, counts | L/D | Sink, m/s | Props' efficiency | Shaft a motor, W | One out: thrust left | climb, m/s | yaw, N m | tail CL | Brace pull at 4 g, N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| front | 2 | 200 | 0.33 | 20.8 | 72 of 160 | 1.8 | 28.6 | 0.507 | 55% | 644 | 50% | 1.2 | 37 | 1.21 **over** | 1080 |
| back | 2 | 200 | 0.33 | 20.8 | 17 of 160 | 1.8 | 28.6 | 0.507 | 55% | 650 | 50% | 1.2 | 37 | 1.21 **over** | 1080 |
| both | 4 | 535 | 0.58 | 21.3 | 39 of 160 | 3.3 | 28.5 | 0.508 | 52% | 350 | 75% | 2.1 | 19 | 0.62 | 1075 |

## How long the body can be

The tail cone stretched, the nose and the parallel middle as they are. The cubic, held to its closing angle, can be drawn out to 3.07 m overall; past that it swells beyond the body's radius. At each length the V-tail is the size its two volumes ask for on that arm, and the shell's and tail's weights follow their areas. The first row is this variant as its design file has it.

| Length, m | Fineness | Tail arm, m | Tail, m^2 | Volumes, horizontal and vertical | Body skin, m^2 | Body, counts | Tail, counts | All-up, kg | Tail cone's steepest, deg | L/D | Sink, m/s | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.3 | 7.7 | 1.59 | 0.31 | 0.40, 0.020 | 1.59 | 23 | 19 | 21.3 | 10.9 | 28.5 | 0.508 | as designed |
| 1.45 | 4.8 | 0.74 | 0.67 | 0.40, 0.020 | 1.00 | 14 | 41 | 20.0 | 16.0 | 27.1 | 0.536 |  |
| 1.6 | 5.3 | 0.89 | 0.56 | 0.40, 0.020 | 1.10 | 15 | 34 | 20.1 | 13.3 | 27.6 | 0.525 |  |
| 1.8 | 6.0 | 1.09 | 0.45 | 0.40, 0.020 | 1.23 | 17 | 28 | 20.4 | 11.3 | 28.1 | 0.517 |  |
| 2 | 6.7 | 1.29 | 0.38 | 0.40, 0.020 | 1.37 | 20 | 23 | 20.7 | 11.0 | 28.3 | 0.512 |  |
| 2.2 | 7.3 | 1.49 | 0.33 | 0.40, 0.020 | 1.52 | 22 | 20 | 21.1 | 10.9 | 28.5 | 0.509 |  |
| 2.3 | 7.7 | 1.59 | 0.31 | 0.40, 0.020 | 1.59 | 23 | 19 | 21.3 | 10.9 | 28.5 | 0.508 |  |
| 2.4 | 8.0 | 1.69 | 0.29 | 0.40, 0.020 | 1.67 | 24 | 18 | 21.5 | 10.9 | 28.5 | 0.508 |  |
| 2.6 | 8.7 | 1.89 | 0.26 | 0.40, 0.020 | 1.84 | 27 | 16 | 21.9 | 10.9 | 28.5 | 0.508 |  |
| 2.8 | 9.3 | 2.09 | 0.24 | 0.40, 0.020 | 2.01 | 29 | 14 | 22.4 | 10.9 | 28.5 | 0.509 |  |
| 3 | 10.0 | 2.29 | 0.22 | 0.40, 0.020 | 2.19 | 32 | 13 | 22.9 | 10.9 | 28.4 | 0.511 |  |
| 3.2 | 10.7 | 2.49 | 0.20 | 0.40, 0.020 | 2.38 | 35 | 12 | 23.5 | 10.9 | 28.2 | 0.514 | swells |

## How long the wing can be

The outer panels stretched, the braces at the same share of the half-span, the tubes as they are. A span passes while nothing is over 1.00 at ultimate and the tip rises no more than 8% of the half-span in the pull-up.

| Span, m | Area, m^2 | Aspect ratio | All-up, kg | Brace, mm | Most-used tube | Joiner | Tip's rise | What limits | L/D | Sink, m/s | Vertical tail volume | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4.8 | 1.60 | 14.4 | 20.0 | 1127 | 0.35 | 0.13 | 1.2% | brace (buckling, night wings, -2 g), 0.35 | 24.8 | 0.58 | 0.0200 | ok |
| 5.4 | 1.79 | 16.3 | 20.6 | 1275 | 0.51 | 0.12 | 1.5% | brace (buckling, night wings, -2 g), 0.51 | 27.0 | 0.54 | 0.0200 | ok |
| 6 | 1.97 | 18.3 | 21.3 | 1422 | 0.71 | 0.24 | 1.8% | brace (buckling, night wings, -2 g), 0.71 | 28.5 | 0.51 | 0.0200 | ok |
| 6.6 | 2.16 | 20.2 | 21.9 | 1571 | 0.95 | 0.27 | 2.1% | brace (buckling, night wings, -2 g), 0.95 | 29.6 | 0.49 | 0.0200 | ok |
| 7.2 | 2.34 | 22.1 | 22.5 | 1719 | 1.25 | 0.30 | 2.5% | brace (buckling, night wings, -2 g), 1.25 | 30.4 | 0.48 | 0.0200 | **over** |
| 7.8 | 2.53 | 24.0 | 23.1 | 1868 | 1.61 | 0.33 | 3.0% | brace (buckling, night wings, -2 g), 1.61 | 30.8 | 0.47 | 0.0200 | **over** |
| 8.4 | 2.72 | 26.0 | 23.8 | 2017 | 2.03 | 0.35 | 3.4% | brace (buckling, night wings, -2 g), 2.03 | 31.0 | 0.47 | 0.0200 | **over** |
| 9 | 2.90 | 27.9 | 24.4 | 2166 | 2.52 | 0.38 | 3.9% | brace (buckling, night wings, -2 g), 2.52 | 31.0 | 0.47 | 0.0200 | **over** |
| 9.6 | 3.09 | 29.8 | 25.0 | 2316 | 3.08 | 0.41 | 4.5% | brace (buckling, night wings, -2 g), 3.08 | 30.9 | 0.47 | 0.0200 | **over** |
| 10.2 | 3.27 | 31.8 | 25.7 | 2465 | 3.73 | 0.44 | 5.0% | brace (buckling, night wings, -2 g), 3.73 | 30.8 | 0.47 | 0.0200 | **over** |

What stops the wing is the 12 mm brace tube buckling in the push-over as the brace gets longer. At 6.0 m it is
at 0.71 of its buckling load. Both variants carry the same 6.0 m wing, so they share outer panels.

## The drag

Counts of 0.0001 on the wing's area, by the paper's build-up, for the twin:

| Speed, m/s | CL | Wing | Braces | Tail | Body | Pods | Induced | L/D | Sink, m/s | L/D, no braces | Sink, no braces |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 14.5 | 0.82 | 90 | 22 | 19 | 23 | 3 | 131 | 28.5 | 0.51 | 30.9 | 0.47 |
| 16.5 | 0.63 | 86 | 21 | 18 | 22 | 3 | 78 | 27.7 | 0.59 | 30.6 | 0.54 |
| 18.5 | 0.50 | 83 | 20 | 17 | 22 | 3 | 49 | 25.9 | 0.71 | 29.0 | 0.64 |

It is optimistic: no interference, gaps, antennas, jury struts or stopped propellers.

## The parts

`osprey recon-sailplane` writes `scad/params.scad` from the design file, beside the modules in
[`src/osprey/recon/scad`](../../src/osprey/recon/scad). Change the design file, not the SCAD.

| File | What it draws |
|---|---|
| `assembly.scad` | The whole aircraft, with the variant's tail, pods, booms and props; `-D see_inside=true` clears the skin and takes the brace fairings off |
| `brace_fittings.scad` | A brace's fittings where they go: the fork under the wing, the root fork on the bulkhead, the jury strut's fork and collar, the tube ends. `-D part="wing_fork"` and so on give one for the printer |
| `end_rib.scad` | The centre section's end rib: the spar's mouth for the joiner, and pockets for the MPX and XT30 connectors in the mating face |
| `center_wing.scad` | The SD7037 lofted over the two spars: skin, ribs, flaps with hinge pockets, and the root fairing |
| `nadir_belly.scad` | The belly shell with a flat for the camera: a 110 mm window, the pane's recess, bosses for a camera plate |

![A brace with its fairing off: the tube, its end fittings, the jury strut and its collar](../img/recon-sailplane-brace.png)

- **Tube ends.** A bonded socket 20 mm deep with two adhesive grooves, and a tang for the pin.
- **Forks.** The wing and jury forks are cradles bonded round the lower half of the square spar, with two
  cheeks down to the pin. The root fork bolts to the front main bulkhead through the hull.
- **Flaps.** Hinged on the lower surface at 75 % chord. Fully down as brakes, a flap's trailing edge is
  below the body's crown, so the flaps start outboard of the fairing and the trailing edge over the body is
  fixed.
- **Belly flat.** The body is cut by one plane through the hull at the pane's two ends, 7.8° nose-up. A
  convex body cut by a plane leaves a flat with no step.

![From below: a brace's aerofoil fairing, the jury struts and the camera's window](../img/recon-sailplane-below.png)

## Not done

- The parts build in OpenSCAD as closed solids (the tests export them), but none has been sliced or printed.
  The pods, booms, tails, root fairing and outer panels are drawn for the look, not for making.
- The outer panels' structure, the tails' structure, the hatch and the wing's saddle pins are not designed.
- The lift is a vortex lattice's: no section polars, so no stall or bubble, and no body. No trim, gust,
  landing or flutter case. A braced wing this slender, and booms, want an aeroelastic check.
- The props: their wash over the wing, braces and tailplane, the thrust's bending of the wing fore and aft,
  a back prop's clearance from a deflected aileron.
- The CG is only moved, never found: the balance is each variant against the package, not against the wing.
- The braces' roots, and the boom's lower fin tips, are low on a belly-landing aircraft.
- Bond and fitting strength are not checked, beyond the pins' bearing.
