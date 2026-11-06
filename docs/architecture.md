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
  shape, gives the full 6-DoF masthead pose relative to the hull, the way
  hydra-vision's Pointer engine registers against a fiducial map.

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
