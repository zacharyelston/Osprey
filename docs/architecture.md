# Osprey architecture

Osprey is a mast-mounted, multi-camera vision system for sailboats. It has two
jobs:

- **spotting and inspection:** see over the horizon and into wave troughs from
  the masthead;
- **look-down:** watch the boat itself and the water around it, to guide
  docking and feed the AI pilot.

It is meant to grow into a whole-boat vision system: deck, cockpit, interior
and dockside cameras feeding the same CV models.

## Why the masthead

| Eye height | Horizon | Boat with 1 m freeboard | Another boat's masthead (15 m) |
|---|---|---|---|
| Deck, 2.5 m | 6.1 km | ~10 km | ~21 km |
| Masthead, 18.9 m | 16.6 km | ~21 km | ~32 km |

Horizon distance matters less than the grazing angle. At 1 km a masthead
camera looks down at the water about 7x more steeply than an eye on deck. That
is what lets it see a person in the water past the crests: in sea state 3 the
masthead sees them about two and a half times as often (`optics.wave_exposure`).
From a known height, the waterline's dip below the horizon also gives the range.
Both are in the same frame, so the mast's motion cancels out.

## Cameras aim with motors, but measure with pixels

The mast swings: about ±3 m at the truck and over 10 deg/s in a moderate sea.
The design does not fight that mechanically to the precision vision needs.
Instead the work is split:

- **Outer gimbal (slow, large angle):** takes out heel, roll and pitch.
- **Inner fast stage (sensor shift or a steering mirror, small angle):** cleans
  up the residual on the long lens.
- **Software:** solves each frame's pose from things in the image. At sea the
  horizon gives roll and pitch. In harbour the deck, a rigid body of known
  shape, gives the full 6-DoF masthead pose relative to the hull, by
  registering against it like a fiducial map.

The pose chain is world, then hull (deck GNSS and IMU), then masthead (deck
registration), then each camera.

## The rig: 1 + 4, in looking groups

- **`top`:** a long-zoom PTZ (6.5-200 mm) with two-stage stabilization, on a
  0.5 m forward crane at the truck.
- **`fwd`, `port`, `stbd`, `aft`:** four mid-zoom PTZs (4.8-120 mm) around the
  mast at lower, staggered heights.

Any 1 to 4 cameras form a **looking group** on one target, while the rig's
`reserve` camera (1 by default) always keeps watch. A group buys three things:

- **resolution:** multi-view super-resolution, capped at 1.4x;
- **visibility:** cameras at different heights see past different crests;
- **range:** a triangulation baseline, with relative orientation fixed against
  the shared horizon or deck.

`tasking.Sim` assigns groups every tick, in priority order. It prefers cameras
the lower-priority tasks need least and charges slew and zoom time on every
reassignment.

## Gecko pods: two eyes, one cable

`gecko5` turns each station into a pod.
- **Top:** a PTZ, as before.
- **Bottom:** a second PTZ, hung upside down.
- **Between them:**
  - a SOC that encodes both streams and runs detection on full-resolution
    frames before compression;
  - a 6-axis IMU that timestamps every frame's attitude;
  - a PoE PD on a single gigabit cable down the mast.

The pod body splits the sphere. The upper eye can't see under the pod and the
lower eye can't see over it, so the pair covers everything from straight down
to 30 deg up. The two eyes point independently. In docking, the lower eyes
take the water round the hull and the upper eyes stay on the horizon
(`calcs.optimize_aims` sends any PTZ that adds nothing to docking back to
watch). The pods use the mast5-spreaders positions. Their electronics, kits
and power and network budgets are in `design/electronics.toml`.

**Watch by sectors.**
- **Sectors:** every pod faces outward from the mast, and its eyes sweep
  their own sector of horizon (120 deg for the lower pods, all round for the
  masthead). Each sector overlaps its neighbours'.
- **The rule:** with `watch = "sectors"`, a looking group may take any eye,
  as long as every bearing a camera can see is still swept by at least one
  watcher. This replaces the fixed reserve camera.
- **Pairs:** a pod's two eyes can be slaved to one target, or each can pair
  with a neighbour on the mast.
  - Pairs within a pod share a rigid body: no mast flex between them
    (20 urad), but only a 0.36 m baseline.
  - Pairs across pods have metres of baseline, and need the pod gyros to
    hold 50 urad.

What the pod electronics are for:
- **Gyros, not just accelerometers.** Aloft, the mast's own acceleration
  swamps gravity's direction: accelerometers alone get tilt wrong by about
  28 deg (p95) at the masthead in sea state 4.
- **Mast flex.** The mast's 2.4 Hz bending moves the masthead pod against the
  gooseneck pod by about 850 urad (p95). That is far beyond the 50 urad a
  stereo pair needs, and too fast for 5 Hz horizon fixes to follow. Each pod's
  gyro measures its own flex between fixes, bringing it back to about 57 urad.
- **PTP time.** Hardware-timestamped PTP holds shutter sync to about 1 us,
  i.e. under 1 urad of pointing at the mount's angular rate. Software
  timestamps would cost about 370 urad.
- **Compute on the pod.** Two 4K30 sensors make 6 Gb/s raw, six times one
  gigabit link. Frames must be encoded on the pod, and small far targets are
  best found before compression smears them.

An earlier version put a fixed 190 deg fisheye under each pod. It gave 97 %
two-view docking coverage with no aiming, but its 1.1 mrad pixels gave 14 cm
depth at the hull edge, and it couldn't join the horizon watch.
`runs/2026-11-06_pods-fisheye-sweep` has its reports. The fisheye camera class
and its cube-face renderer stay for deck, cabin and dockside cameras.

## Spreader pairs: dual mounts fore and aft

`spreader-pairs` puts a back-to-back dual mount at each spreader tip: a fixed
4K bullet looking forward and another aft, each with its own PoE cable and
encoder, and no pod computer or IMU. The masthead keeps its gecko pod.

- **Pairs across the boat:** the two forward cameras of a level are a stereo
  pair with the spreaders' span between them (2.7 m low, 1.9 m high), and so
  are the two aft ones.
  - The lower pair is opened to 4 mm and tilted 30° down, for the water round
    the bow and the stern.
  - The upper pair is level, for the horizon ahead and astern.
- **No mast flex between a pair.** Both cameras sit at the same height, so
  the mast's fore-aft bending moves them together (0 µrad in the model;
  spreader twist is not modelled).
- **Shutter sync still matters.** Cameras on their own clocks, about 2 ms
  apart, lose about 370 µrad in sea state 4. Synced shutters, or one box
  grabbing both frames, keep it under 1 µrad.
- **What it gives up:**
  - the beams, which go to Recon flying escort;
  - identification at range, since the bullets are fixed 8 mm and the
    masthead's long zoom is the only zoom left;
  - docking coverage alongside, where the pier is.
- **What it gains:** 7.7 kg masthead-equivalent aloft instead of 11.9, and
  259 Ah a day instead of 381.

The pair checks are in `calcs.pair_checks`. Mounts without a computer get
one PoE port per camera (`Pod.ports`).

## The whole boat

A rig is a list of stations, and stations declare the `zones` they serve:
`exterior`, `deck` or `interior`. `whole-boat` includes `mast5` and adds bow
and stern-arch fixed cameras plus saloon and engine-room domes. The tasking,
calcs and renderer take any number of stations, and the renderer writes one
dataset format for all of them.

## Synthetic data for the CV models

`osprey render` drives a MuJoCo scene with the motion model and writes, for
every camera and frame:
- RGB;
- metric depth (uint16, mm);
- a class mask (water, self, dock, piling, boat, person, fender, line, sky);
- `labels.jsonl` with intrinsics and the camera-to-world pose.

The same contract will carry real captures from the Phase 0 pod. Detection,
docking geometry and pose models train on the synthetic data and are checked on
the real captures.

## Phases

0. **Bosun's Chair:** a halyard-hoisted pod with an action camera, IMU and
   GNSS. It measures the real masthead motion spectra that replace the REF
   motion model (`motion.Motion` takes a measured log unchanged).
1. **Look-down docking:** stereo pairs plus deck registration give a costmap
   for the pilot.
2. **Spotting:** horizon-band detection, dip ranging and thermal.
3. **Inspection:** the long-zoom PTZ, cued and slewed to targets.
