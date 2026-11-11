# The Trident: three modules round a core

**Status: first look.** A crewed tailsitter built from three identical modules, from a SketchUp massing sketch
(trident-1). Every input is a REF stand-in, in [`design/trident.toml`](../../design/trident.toml), so the numbers
show which way the design should move, not what to build. The run behind this page is
[`runs/2026-11-11_trident`](../../runs/2026-11-11_trident/trident.md).

![The Trident's righting curves for the sketch, the sketch balanced and the found layout; where the found layout's weight goes, crewed and as cargo; and the three afloat from the side](../img/trident.png)

## The idea

- **Three identical modules.** Each is an arm and a wing panel, a motor pod with a big slow prop, and a leg with a
  foot. The third module is extra on purpose:
  - it gives control authority in any attitude;
  - it is the fin in flight, so any of the three can be up;
  - a module unbolts and swaps, so it is serviceable and easy to adapt.
- **The core.** Sized round a 4x8 ft sheet: 1.22 m across and 2.44 m long inside. It has 15–20 cm foam walls and
  an aeroshell nose. Inside, one person and 100 kg of mission load ride in a padded, buoyant container.
- **The power cells.** They sit in a bay a metre long under the core: the keel afloat and the tail in flight.
- **The flight.** It lifts off standing on its tail, tips over and flies on the three wings in a Y, then lands
  back on its feet.

## The sketch

The SketchUp sketch is primitive shapes for the mass:
- three 4.57 m (15 ft) discs round a 1.22 m column 2.13 m tall;
- triangular webs from the column's foot up to each rotor;
- a 1 m bay below.

The model keeps the discs and adds what the sketch left out:
- the foam walls and their skin;
- the aeroshell;
- the wings under the props;
- the legs and feet;
- the battery sized for a trip.

The trip is 4 min of hover, 50 km of cruise and a 10 min reserve.

## What the numbers say

| | As sketched | Balanced | Found |
|---|---|---|---|
| Max weight (crewed) | 1,112 kg | 1,068 kg | 888 kg |
| Props' plane, up the axis | 3.80 m (the core's top) | 1.81 m | 1.70 m |
| Static margin | −1.52 chords: can't fly | +0.10 | +0.10 |
| Hover / cruise | 161 / 105 kW | 152 / 96 kW | 115 / 65 kW |
| Upright afloat (GM) | −1.2 m: falls over | 3.1 m | 5.9 m |
| Always comes back upright | no | no: held over at 70–90° | yes, least arm +4 cm |

- **As sketched, the module ring is in the wrong place, both for flight and for floating.**
  - With the props at the core's top, the wing sits 1.5 chords ahead of the centre of gravity. A tailsitter
    needs the CG just ahead of the wing, so it can't fly.
  - The same 230 kg of motors, props, pods and wings 3.8 m up puts the CG too high to float upright.
  - The 1 m float-feet sit wholly under water, so they give it no stance.
- **Balanced: slide the module ring down the core until the wing sits on the CG.** The props' plane drops to
  about 1.8 m up the axis, just above the core's floor.
  - That makes it flyable, and 44 kg lighter.
  - The wing panels now reach down into the water afloat. Foam-cored and buoyant, they are the floats.
- **The float-feet then make it worse.** Their buoyancy sits at the tail, the end that must sink for it to come
  back upright, so they hold it lying over. Every foot tried, from 15 x 80 cm to 25 x 160 cm, fails to right it.
  The legs still stand it on deck, but they end in pads, and the wings float it.
- **Found: balanced, with a glass skin, legs with pads, longer and narrower wings and the person crouched.**
  - **Weight:** 888 kg, carrying one person and 100 kg; uncrewed, 246 kg of cargo.
  - **Battery:** 41 kWh (204 kg), filling 13 % of the bay.
  - **Hover:** 115 kW, at a disc loading of 18 kg/m², about a third of a light helicopter's, with 8.5 m/s of
    downwash.
  - **Cruise:** 49 m/s on 65 kW.
  - **Afloat:** it rights itself from every angle and every direction, crewed and as cargo. The margin is thin: its
    least righting arm is +4 cm.

## What drives it

- **HDPE is heavy.** Wrapping 18 cm foam walls in 3 mm HDPE makes the core's walls weigh 176 kg. A glass-epoxy
  sandwich over the same foam is 116 kg. With the weight closed round it (the battery shrinks too), the craft comes
  out about 100 kg lighter.
- **Big props pay twice.** 4.57 m props against 3.05 m:
  - hover drops from 202 to 115 kW;
  - the craft gets 100 kg lighter.

  The cost is size: 10.8 m across the prop tips.
- **Crouching matters.** The person crouched low (the container's centre 0.5 m above the floor) rights itself;
  sitting up (0.9 m) it doesn't.
- **The wing is a float as well as a wing.** A panel running out 90 % of a prop radius past the motor, with a
  0.8 m chord, rights it.
  - A shorter panel gives less stance.
  - A deeper chord puts more buoyancy at the tail and holds it over.
- **Range.** Crewed, a 25 km trip needs 814 kg of craft; 100 km needs 1,091 kg. Flown uncrewed, the 50 km airframe
  carries 297 kg of cargo over 25 km, or 144 kg over 100 km.

## Watch-outs

- **The props sit 74 cm above the water afloat.** That is too little in a sea; on deck they are at head height.
- **The core's floor is only 4 cm above the waterline.** The hatch and any seams want to be well above it.
- **The wings sit in the water at rest.** Lifting off must break them free, and suction and spray on the wings
  aren't modelled.
- **The static margin counts the wing only.** The core ahead of it (destabilising) and the legs behind it
  (stabilising) are left out.

## Not modelled yet

- **Flight:** the transition, control in the props' wash, and a crewed tailsitter's ergonomics. The person rotates
  90° between hover and cruise.
- **The tail:** legs as fins, or strakes at the feet.
- **Waves and dynamics:** the righting curves are static, in calm water.
- **Structure:** the arm's and wing's spar sizing; here they are weight per area.
- **The module joint:** how a module bolts on and what that costs in weight.

## Running it

```bash
uv run osprey trident --workers 8    # three layouts, the cargo case and the sweeps, about 25 s
```
