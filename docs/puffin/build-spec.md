# The spar Puffin, SAR build: a build spec

**Status: first article, to build and test.** This is the first float/fly/land craft to build, chosen in the
[market study](markets.md). It is a search-and-rescue UAS that launches from any boat, searches for a person in
the water, lands beside them to mark them, and is recovered by boathook.

It is the [spar Puffin](README.md) with the SAR kit aboard:
- a bigger battery in place of the ballast;
- a fuller girth;
- its wing swept forward 25°, flying 1.0 m props.

The numbers come from the SAR layout ([`design/recon/puffin.toml`](../../design/recon/puffin.toml) `[layouts.sar]`
and `[sar]`) through `uv run osprey recon-puffin-sar`. The kept run is
[`runs/2026-11-11_recon-puffin-sar`](../../runs/2026-11-11_recon-puffin-sar/sar.md).
- **The righting is modelled.** It uses the same meshes and curves as the spar Puffin study.
- **The flight numbers are first-order:** momentum theory and a drag polar. The hover rig and first flights in
  the test plan below replace them.

## The job

1. **Launch.** A lifeboat, an offshore wind farm's crew transfer or service vessel, or a yacht puts it over the
   side. It floats tail-down and lifts straight off the water.
2. **Fly out and search.**
   - It flies to the datum, the casualty's estimated position, at about 22 m/s (43 kn).
   - It searches with its EO/IR gimbal, the same search model as Osprey Recon's `sar-datum` and `sar-offshore`
     missions ([recon.md](../recon.md)).
3. **Mark.**
   - It drops the rescue tube to the person.
   - It lands beside them and floats as a marker: an AIS-MOB beacon, a strobe, and a camera on the horizon.
   - It holds that for a day or more, while the boat comes.
4. **Recover.** The crew picks it up by boathook, or it flies back if the person was found by other means.
5. **Survive.** If a wave knocks it flat at any point, it bobs back upright.

## Requirements

| # | Requirement | Value | Status in the model | Verified by |
|---|---|---|---|---|
| R1 | Mass, ready to fly | 8–10 kg | 9.12 kg | weighing |
| R2 | Floats tail-down, its launch attitude | stays upright on its own | 52 cm under water | tank test T1 |
| R3 | Rights itself from any knockdown, with the rescue tube aboard and after it is dropped | GZ above zero from 0° to 180°, onto its belly and onto a wingtip | yes and yes: +1.2 cm at 15°, +40 cm at 90° | tank test T1 |
| R4 | Props clear the water afloat | ≥ 25 cm upright, ≥ 15 cm rolled 15° | 43 cm and 29 cm | tank test T1 |
| R5 | Launches from the water in sea state 3 | lift-off and transition | not modelled for this airframe (the earlier tailsitter launched in 4.2 s) | T4, T6 |
| R6 | Searches the `sar-datum` job (3 km, 30 min task) and still marks | the search plus ≥ 12 h afloat | 50 min of search affordable, 33 h afloat after a 30 min search | T5, T6 |
| R7 | Reaches the `sar-offshore` job (10 km) | out, search and mark | 45 min of search affordable; marking then needs search time held back (see below) | T5 |
| R8 | Drops a rescue tube | a self-inflating tube, 0.4 kg with its release | slung under the wing at the flight CG | T5 |
| R9 | Marks the casualty | AIS-MOB, strobe, GNSS position over the datalink | dome, highest point afloat, 78 cm up | T3, T6 |
| R10 | Survives losing a motor or all power | it reaches the water slowly enough to float again | 5 m/s under a 2.5 m parachute (see below) | T7 |
| R11 | The screw fails safe | battery runs to the boom whenever power is lost | back-drivable ball screw, brake released by power loss | T2 |
| R12 | Salt water | the lower metre and the motors sealed | IP67 motors, sealed hull | soak and spray tests |
| R13 | Recovery | by boathook from a small boat's side | a lifting eye at the dome | T6 |

## The build point

| | |
|---|---|
| Hull | a spar 1.30 m long, a 45 cm girth at the waterline, the boom at the tail 11 cm across |
| Wing | 1.60 m span, 0.26 m chord, swept forward 25°; the root's leading edge 57 cm up the hull, the mean chord at 70 cm; free-flooding |
| Props | two, 1.00 m, at the wingtips; 7.5 cm clear of the hull's side |
| Tail | four strakes on the boom, an X: the tail in flight, the legs on a deck |
| Battery | 3.5 kg on a ball screw: 10 cm up from the tail afloat, 47 cm further up in flight |
| Mass | 9.12 kg, 8.72 kg after the tube is dropped |
| Afloat | 52 cm under water; props 43 cm clear; the dome 78 cm above the water |
| Hover | 780 W, 390 W a motor; disc loading 5.8 kg/m²; each motor peaks near 790 W at 1.6× thrust to weight |
| Cruise | stalls at 17 m/s; cruises at 22 m/s on 580 W |
| Endurance | 665 Wh pack, 532 Wh usable; 26 Wh to launch and land; then 52 min of cruise, about 70 km |
| Afloat, marking at 6 W | 89 h on a full pack; 33 h after a 30 min search 3 km out |

### Mass budget

| Part | kg | Where |
|---|---|---|
| Hull, moulded, the boom and the lifting eye | 1.59 | the length of the spar |
| Battery, 12S Li-ion 21700, about 190 Wh/kg as a pack | 3.50 | on the screw |
| Dome: EO/IR gimbal 0.30, AIS-MOB, strobe and antennas 0.20 | 0.50 | the nose |
| Autopilot, radios, ESCs 0.60; the screw drive 0.25 | 0.85 | low in the boom |
| Strakes | 0.30 | the boom |
| Wing, free-flooding | 1.10 | 57–83 cm up, swept |
| Motors, two | 0.60 | the wingtips |
| Props, two, 1.0 m | 0.28 | the wingtips |
| Rescue tube and release | 0.40 | under the wing, at the flight CG |
| **Total** | **9.12** | |

## Subsystems

- **Hull.**
  - A moulded composite spar, sealed below the dome's joint.
  - The boom is the keel: the battery runs in it.
  - The girth flares at the waterline and rounds into the dome.
  - A lifting eye at the top of the dome takes the boathook and a crane hook.
- **Wing.**
  - It free-floods: drained and vented, not sealed. Lying flat in the water it then doesn't hold the craft there.
    This is what makes the spar right itself.
  - It is swept forward 25° with a carbon spar. At 22 m/s and this size, the divergence that forward sweep
    invites is a stiffness check, not a design driver.
  - Elevons sit in the props' wash for control in hover, as on the Puffin.
- **Propulsion.**
  - Two ~1 kW outrunner motors, IP67, at the tips, turning 1.0 m fixed-pitch props.
  - They spin up in spray, so they must be sealed for salt.
- **The battery on a screw.**
  - A back-drivable ball screw with a power-off brake.
  - The travel is 47 cm. At 5 cm/s that is about 10 s, run in hover after lift-off and before landing.
  - With power lost, the brake releases and gravity runs the battery to the boom whenever the craft is nose-up.
  - Lying flat, gravity doesn't pull along the hull, so a spring return or the drive's own power brings it home.
- **Autopilot.**
  - An open autopilot with dual-motor tailsitter support: ArduPilot's QuadPlane tailsitter mode flies hover on
    the props' thrust and the elevons.
  - It runs the screw as a scripted function, which is the new work: the battery runs forward before the
    transition and back after it.
  - The sensors: dual GNSS, an airspeed sensor, and a water switch to know it is afloat.
- **Datalink.** A long-range telemetry and video radio, with the antenna in the dome.
- **SAR payload.**
  - An EO/IR gimbal of 0.3 kg in the dome.
  - A type-approved AIS-MOB beacon and a strobe at the top of the dome.
  - A self-inflating rescue tube on a servo release under the wing.
  - Keep the dome at 0.5 kg or less: weight there costs righting. Heavier dome payloads need ballast or more
    girth (the [screw sweep](README.md)).

## The sequence, and the screw

| Phase | The battery | Notes |
|---|---|---|
| Afloat, waiting | in the boom, 10 cm up | deep draft, rights itself |
| Lift-off | in the boom | a wave's quiet moment; climb clear to 3 m |
| Hover, 10 s | runs forward 47 cm | the CG climbs to the wing |
| Transition | forward | pitch over, accelerate past 17 m/s |
| Cruise and search | forward | the CG on the wing, 10 % static margin |
| Drop | forward | the tube is at the flight CG: no trim change |
| Transition back, hover | runs back to the boom | then settle on the water |
| Marking | in the boom | sleep at 6 W: AIS-MOB, strobe, the radio listening |

## Losing power

- **The screw alone loses power.** The battery runs down the boom and the CG goes behind the wing. In wing-borne
  flight it pitches up to tail-first, but that is its hover attitude. With the motors running it hovers and lands
  on the water. So the screw failing ends the flight but doesn't crash the craft.
- **All power is lost.** Then it falls boom first, like a torpedo. How fast it meets the water
  ([run](../../runs/2026-11-11_recon-puffin-sar/sar.md)):

| Slowed by | Hits the water at | Like a drop of | Costs |
|---|---|---|---|
| nothing | 50 m/s | 129 m | the airframe |
| the props windmilling | 13 m/s | 9 m | nothing |
| the props autorotating on collective pitch | 8 m/s, about 0 after an ideal flare | 4 m | variable-pitch hubs on both props |
| a 2.5 m parachute | 5 m/s | 1.3 m | 0.5 kg |

For the UAS, **the parachute** is the simple answer:
- It is half a kilogram.
- It fires on a separate power supply.
- It puts the spar into the water boom first at 5 m/s. The spar is shaped for exactly that entry, and floats
  and rights itself afterwards.

Flaring the rotors needs collective pitch on both props. That is where a crewed craft would have to go, because
a parachute alone is a poor answer for a person aboard. The flare figure is ideal: the props' stored energy fully
spent. Real props will do worse.

## Options weighed

**Forward sweep (adopted, 25°).** The mean chord is held where the straight wing had it, so the tips and props go
up the hull and the root comes down:

| Sweep | Props clear afloat | Rolled 15° | Battery travel | GZ at 15° | Longest props |
|---|---|---|---|---|---|
| 0° | 30 cm | 16 cm | 50 cm | +1.5 cm | 1.09 m |
| 25° | 43 cm | 29 cm | 46 cm | +1.2 cm | 1.09 m |
| 45° | 58 cm | 44 cm | 42 cm | +0.7 cm | 1.13 m |

- **Sweep's real gain is keeping the props out of the water:** 13 cm at 25°, which matters most when it rolls in
  a sea.
- **It shortens the battery's travel only a little:** 4 cm at 25°.
- **It costs a little righting.** The wings flood, so the tips' mass goes up the hull with no buoyancy to pay for
  it.
- **Longer props come from the span, not the sweep.** Even a straight wing takes 1.09 m props before they reach
  the hull. Going from 0.76 m to 1.0 m props cuts hover power by about a quarter, from 1,007 W to 780 W. Only
  past 45° do the props move up beside the rounded nose and grow further.

**An X-wing quad: four forward-swept panels, four 1.0 m props (not adopted for the UAS).** A first-order
estimate, with two more motors and props and a centre fitting:

| | Two props | X-wing, four props |
|---|---|---|
| Mass | 9.1 kg | about 10.2 kg |
| Hover | 780 W | about 650 W |
| One motor lost in hover | it can't stay level: the parachute | it lands on the two diagonal motors, about 460 W each |
| Installed motor power | about 1.6 kW | about 1.8 kW, sized for losing one |

- **For the UAS, the parachute covers a motor loss** at less mass and complexity.
- **For a crewed craft the X-wing is the better path.** Its rotors can lose one motor and still land, and that is
  the step from sketchy toward human-rated.
- **Not modelled here:** the X-wing's righting, with four panels and four tip masses round the hull.

**An engine genset (not in the airframe).** A Honda EU2200i-class inverter genset makes 1.8 kW rated and weighs
21.5 kg dry. It runs 3.2 h at rated load on a 3.6 L tank, for about $1,100.
- **It can't fly in the UAS.** It weighs more than twice the whole craft.
- **On the boat it is the right tool.**
  - It recharges the 665 Wh pack in about 25 minutes.
  - With three packs it keeps one craft flying all day.
  - It is durable, cheap, everywhere and field-replaceable.
- **On a full-size craft that spends hours afloat between short flights, it can earn its place.** Carried with
  its fuel, it beats a 300 Wh/kg battery only on runs longer than about four hours: 290 Wh/kg at 4 h, 410 at 6 h.
  It would recharge the pack while the craft floats, the battery-hop arrangement in the [Beet study](../beet/README.md).
- **It can't carry a hover.** At 1.8 kW it is 4% of the full-size Puffin's 45 kW hover.

## Test plan

| # | Test | Pass |
|---|---|---|
| T1 | **Tank.** A ballasted hull at full mass, wings on, knocked to every angle onto its belly and onto a wingtip; again with the tube gone; again with the wings flooded | comes back upright from every angle; floats within 3 cm of the modelled waterline; props ≥ 40 cm clear |
| T2 | **Screw bench.** Full travel with the 3.5 kg battery, nose-up and level; cut power at every station | 47 cm in ≤ 12 s; with power cut nose-up, it runs to the boom; lying flat, the spring or drive returns it |
| T3 | **Soak.** 24 h afloat in salt water, marking at 6 W | no leaks; the AIS-MOB is received at 5 nm; the measured draw sets the marking hours |
| T4 | **Tethered hover off the water**, in a pool or a still lake | lifts off, runs the battery forward, hovers, runs it back and settles; measured hover power within 15 % of 780 W |
| T5 | **Free flight over a lake:** transitions, cruise, a timed search pattern, the tube dropped | cruise power and stall measured; transition clean both ways; the tube lands within 10 m of the target |
| T6 | **At sea, sea state 1 to 3:** launched from a RIB, a search with a thermal dummy, marking, and boathook recovery | lift-off in waves; finds the dummy; marks it; the crew recovers it without stopping the engine |
| T7 | **Power loss:** a parachute deployment from height over water, and a single-motor cut in hover low over water | enters boom first under 6 m/s, floats and rights itself; with a motor cut the parachute fires and it survives |

## Rules

- **Flying it.**
  - In the US it flies under Part 107. Searching 3–10 km out means flying beyond line of sight, which needs a
    waiver until Part 108 is final.
  - In the EU it needs the Specific category under a SORA risk assessment. Launching from a moving boat needs a
    full SORA rather than a predefined scenario.
  - The [market study](markets.md) has the detail.
- **The beacon.**
  - Use a type-approved AIS-MOB unit.
  - Check with the radio authority before transmitting AIS from the air. Afloat it is doing what the unit was
    approved for.

## Not modelled

- The transition, the take-off from waves, and the forward-swept wing's own aerodynamics. The drag polar is a
  first-order guess.
- Waves on the righting, and the ride afloat: the righting near upright is soft, about a centimetre at 15°, so it
  will rock.
- The X-wing's righting.
- How long the search planner actually needs. The missions charge the full task time as an upper bound.
- How much search time to hold back so the marking lasts a set number of hours on the 10 km job.

## Running it

```bash
uv run osprey recon-puffin-sar --workers 8    # out/recon-puffin-sar: sar.md, sar.json
uv run osprey recon-puffin --workers 8        # the spar Puffin's layouts and screw sweep, now with the SAR layout
```
