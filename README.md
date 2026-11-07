# Osprey

**Camera pods on a sailboat's mast that keep watch over the whole horizon, find a
person in the water, and guide the boat into a slip. Designed in simulation first.**

<p align="center">
  <img src="docs/img/gecko-docking-sheet.png" alt="Synthetic frames from all ten pod cameras and an overview, docking into a slip" width="100%">
</p>

<sub>Frame 50 of a synthetic docking run on the `gecko5` rig
([`runs/2026-11-06_gecko-docking-render`](runs/2026-11-06_gecko-docking-render/)). Each pod has an upper
and a lower camera. The upper eyes `top`, `fwd` and `aft` keep the horizon watch while the lower eyes
take the dock. The `port` and `stbd` upper eyes, aimed across the boat, mostly see their own pod (red).
Every frame also comes with metric depth, a class mask and the camera's exact pose.</sub>

> **Status: screening models, not specifications.** Every input is a REF stand-in: a reference 40 ft
> sloop, typical camera classes and typical electronics, all in [`design/`](design/). The numbers
> below show which way the design should move. Real measurements replace them in Phase 0.

## What Osprey is

| | |
|---|---|
| **Osprey Nest** | Mast-mounted camera "gecko pods". Each pod carries a PTZ camera on top and a second one hung underneath, with a computer (SOC), a 6-axis IMU and PoE between them. Pods face outward from the mast and sweep overlapping sectors of the horizon. They serve horizon watch, man-overboard (MOB), docking and guidance for an AI pilot. This repository is mostly Nest. |
| **Osprey Recon** | A 3D-printed drone for search and rescue. In progress: work has just started in [issue #1](https://github.com/zacharyelston/Osprey/issues/1). No results yet. |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/nest-layout-dark.png">
  <img src="docs/img/nest-layout.png" alt="Side view of the mast with five pods at 18.75, 13.85, 12.25 (port and starboard) and 2.55 m, and a plan view of their overlapping 120 degree watch sectors plus the all-round masthead sector">
</picture>

<sub>The `gecko5` rig from [`design/rigs/gecko5.toml`](design/rigs/gecko5.toml): five pods (ten cameras)
at the positions of the earlier spreader rig. Port and starboard sit on the upper spreader tips.</sub>

## Key findings

From the kept sweeps of 2026-11-06 ([`gecko-sweep`](runs/2026-11-06_gecko-sweep/summary.md),
[`first-sweep`](runs/2026-11-06_first-sweep/summary.md)).

<table>
<tr>
<td align="center" width="20%"><h3>100 %</h3>of the time the whole horizon is swept under sail, 8 s worst revisit<br><sub>gecko5; 0 % for both single-camera rigs</sub></td>
<td align="center" width="20%"><h3>2,044 m</h3>to detect a person in the water from the masthead in sea state 3<br><sub>249 m with the same camera at deck height</sub></td>
<td align="center" width="20%"><h3>96.5 %</h3>of the water within 3 m of the hull seen by two cameras when docking<br><sub>4.6 cm stereo depth (p95) at the hull edge</sub></td>
<td align="center" width="20%"><h3>57 µrad</h3>between pods with gyros, against 846 µrad of mast flex without<br><sub>sea state 4, masthead to gooseneck</sub></td>
<td align="center" width="20%"><h3>11.9 kg</h3>masthead-equivalent mass aloft, against a 4 kg budget<br><sub>the next design problem</sub></td>
</tr>
</table>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/rig-compare-dark.png">
  <img src="docs/img/rig-compare.png" alt="Bar chart comparing gecko5, mast5-spreaders and mast5 on five measures">
</picture>

The three rigs share the boat and the scenarios. `mast5` and `mast5-spreaders` have one PTZ per station
and keep one camera in reserve for watch. `gecko5` has two PTZs per pod and watches by sectors.

### 1. Height pays, mostly through the waves

The same long-zoom PTZ sees a person in the water at 2,044 m from the masthead and at 249 m from deck
height in sea state 3. In sea state 4 it is 793 m against 100 m. Both are limited by waves hiding the
target, not by pixels. From 18.9 m the camera looks down past the crests.

<img src="docs/img/reach.png" alt="Detection range against eye height for five target classes" width="70%">

### 2. Under sail, the sails blind cameras on the mast. Sectors fix that

Heeled 15° with main and jib up, the sails hide the lee side from cameras on mast brackets. On `mast5`,
only 68.1 % of the horizon is seen without the masthead camera. The gecko pods sit on the spreader tips
and at the masthead, so ten eyes cover 100 % of it, and every bearing lies in two or more watch sectors.

| `mast5`: four cameras on mast brackets | `gecko5`: ten eyes in five pods |
|---|---|
| ![Horizon coverage on mast5](docs/img/coverage-mast5.png) | ![Horizon coverage on gecko5](runs/2026-11-06_gecko-sweep/coastal-watch/gecko5/coverage.png) |

| coastal-watch, need met | buoy | kayak | ferry | sloop | whole horizon swept |
|---|---|---|---|---|---|
| `mast5` | 87 % | 57 % | **0 %** | 96 % | 0 % of the time |
| `mast5-spreaders` | 86 % | 84 % | 86 % | 88 % | 0 % of the time |
| `gecko5` | 80 % | 88 % | 84 % | 99 % | **100 %** (8 s worst revisit) |

### 3. A man-overboard group no longer starves everything else

Any eye can join a *looking group* on one target, as long as every bearing keeps a watcher. In the MOB
scenario every rig gives the person in the water a group of 3 or 4 and meets the need 99 % of the time.
On `mast5-spreaders` that group takes every camera except the reserve, so a buoy 900 m off the bow gets
no camera for the whole five minutes. On `gecko5` the buoy is kept in view 99 % of the time, and the
person in the water still gets a group of 4.

| `mast5-spreaders`: buoy-2 never served | `gecko5`: buoy-2 served by `fwd` |
|---|---|
| ![Looking groups during MOB on mast5-spreaders](runs/2026-11-06_first-sweep/mob/mast5-spreaders/groups.png) | ![Looking groups during MOB on gecko5](runs/2026-11-06_gecko-sweep/mob/gecko5/groups.png) |

### 4. Docking works without giving up the watch

With aims chosen by `calcs.optimize_aims`, the lower eyes see 96.5 % of the 3 m band round the hull with
two cameras. 89 % of the hull edge has a stereo pair, at 4.6 cm depth (p95). The `top`, `fwd` and `aft`
upper eyes stay on the horizon.

| Docking, optimized aims | water band, 2+ cameras | hull edge with a stereo pair |
|---|---|---|
| `mast5` | 94.3 % | 80 % |
| `mast5-spreaders` | 94.6 % | 88 % |
| `gecko5` | **96.5 %** | **89 %** (4.6 cm p95) |
| `pods5`, fixed fisheye under each pod (dropped) | 96.9 % | 91 % (13.6 cm p95 with the scenario aims) |

No mast rig gets more than 91 % of the hull edge into stereo: from the mast, the deck edge hides the
water right against the topsides. That band will need deck-level cameras.

<details>
<summary>More docking detail</summary>

- With the scenario's hand-picked aims, two-camera coverage of the band is only 65.8-75.5 % on the
  one-PTZ-per-station rigs and 75.5 % on `gecko5`.
- The aft camera under the gooseneck sees the coachroof and cockpit, not the water astern. It is a crew
  camera, not a docking camera.
- The fisheye pod needed no aiming, but its 1.1 mrad pixels gave 13.6 cm depth at the hull edge, and it
  could not join the horizon watch. Its reports are in
  [`runs/2026-11-06_pods-fisheye-sweep`](runs/2026-11-06_pods-fisheye-sweep/summary.md).

</details>

### 5. The pod electronics are what make a group work on a bending mast

- **Gyros.** The mast's 2.4 Hz bending moves the masthead pod against the gooseneck pod by 846 µrad
  (p95) in sea state 4. Stereo range at 2 km then degrades from ±14 m to ±221 m. Each pod's gyro between
  5 Hz horizon fixes brings the relative orientation to 57 µrad.
- **Accelerometers alone do not work aloft.** They misjudge tilt by 27.7° (p95) at the masthead,
  because the mast's own acceleration swamps gravity's direction.
- **PTP time.** Hardware-timestamped shutter sync costs 0.18 µrad of pointing. Software timestamps
  would cost 367 µrad.
- **Compute on the pod.** The masthead pod's two 4K sensors make 5,972 Mb/s raw, 6.0x one gigabit
  link. Frames are encoded on the pod (40 Mb/s), and small, distant targets are searched for before
  compression smears them.

## The gecko pod

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/gecko-pod-dark.svg">
  <img src="docs/img/gecko-pod.svg" alt="Diagram of a gecko pod: an upper PTZ, a body holding the SOC, IMU and PoE powered device, and a lower PTZ hung upside down, on one cable down the mast">
</picture>

- **Two eyes that point on their own.** The pod body splits the sphere: the upper eye cannot see under
  the pod and the lower eye cannot see over it. Together they cover everything from straight down to
  30° up. One eye can watch the horizon while the other works the dock.
- **Pairs inside a pod or across pods.** The two eyes of one pod share a rigid body (no mast flex
  between them) but only a 0.36 m baseline. Eyes on different pods have metres of baseline and need the
  pod gyros to hold 50 µrad.
- **One cable.** Power and gigabit Ethernet come up a single PoE cable. The other four pods peak at
  68.1 W, inside 802.3bt Type 4. The masthead pod, with the long zoom, peaks at 81.4 W and does not fit.

The kits, power and network numbers are in [`design/electronics.toml`](design/electronics.toml); the
camera classes in [`design/cameras.toml`](design/cameras.toml). More in
[docs/architecture.md](docs/architecture.md#gecko-pods-two-eyes-one-cable).

### The budgets fail, and they are the next design problem

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/budgets-dark.png">
  <img src="docs/img/budgets.png" alt="gecko5 budgets as a share of their limits: mass, daily energy and masthead power fail; the rest pass">
</picture>

17.8 kg goes up the mast in all, 11.9 kg as a masthead equivalent. Each pod's electronics and housing
weigh 0.92 kg; for all five that is 3.0 kg masthead equivalent. The system draws 12.7 A on watch and 31.9 A active from the 12.6 V house bank, so a day
underway (20 h watch, 4 h active) takes 381 Ah against a 120 Ah budget. Ways down:

- sleep the idle pods on watch;
- go lighter on the lower eyes, or drop the long PTZ at the masthead if a drone (Osprey Recon) takes over
  long-range search;
- power the masthead pod from two cables.

## How the simulation works

```mermaid
flowchart LR
  D["<b>design/*.toml</b><br/>boat, sea, cameras,<br/>targets, rigs, scenarios"] --> M["<b>models</b><br/>frames, motion, optics,<br/>stabilize, occlusion"]
  M --> C["<b>osprey calc</b><br/>PASS / WARN / FAIL checks<br/>and figures"]
  M --> T["<b>osprey sim</b><br/>looking groups,<br/>tasked tick by tick"]
  M --> R["<b>osprey render</b><br/>MuJoCo scene: RGB, depth,<br/>class masks, poses"]
  C --> K["<b>runs/</b><br/>kept results,<br/>with source SHA"]
  T --> K
  R --> K
  R -.-> V["CV models<br/>(detection, docking,<br/>pose; planned)"]
```

<details>
<summary>What each stage does</summary>

1. **Design inputs.** Everything numeric lives in TOML under `design/`. Code never hard-codes a boat or
   a camera. A rig is a list of stations or pods; any number of cameras works.
2. **Models.** Wave spectra drive the boat's roll, pitch, heave and the mast's bending. Optics turns
   pixels on target into detect, recognize and identify ranges (Johnson criteria), including how often
   waves hide a target. Occlusion ray-casts the mast, sails, hull and pod bodies.
3. **Tasking.** `tasking.Sim` assigns looking groups every tick, in priority order, and charges slew
   and zoom time on every reassignment. With sector watch, an eye may leave its sector only while a
   neighbour still covers it.
4. **Checks.** `osprey calc` reports motion, stabilization, reach, ranging, coverage, docking, mass,
   power, network and timing as PASS, WARN or FAIL. It exits 1 on a FAIL, which is a design finding,
   not a crash.
5. **Synthetic data.** `osprey render` drives a MuJoCo scene with the same motion model and writes, for
   every camera and frame, RGB, metric depth, a class mask and `labels.jsonl` with intrinsics and the
   camera-to-world pose. Real captures from the Phase 0 pod will use the same format.

</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/synthetic-frame-dark.png">
  <img src="docs/img/synthetic-frame.png" alt="One synthetic frame from the port lower eye: RGB, metric depth and class mask">
</picture>

<sub>The `port-down` camera at frame 50 of the kept `gecko5` docking render: RGB, metric depth and the
class mask (`self` is our own hull, `boat` the neighbour in the next slip).</sub>

## Quickstart

```bash
uv sync
uv run pytest
uv run osprey calc --scenario coastal-watch --rig gecko5    # PASS/WARN/FAIL checks + figures
uv run osprey sim --scenario mob --rig gecko5               # looking-group timeline
uv run osprey render --scenario docking --rig gecko5        # RGB, depth, class masks, poses
uv run osprey sweep --workers 8                             # every scenario x rig
```

Output goes to `out/` (gitignored). Long sweeps and GPU renders run on two workstations, `gpu1` and
`gpu2`, from a committed snapshot: see [docs/remote-simulation.md](docs/remote-simulation.md).

## Repository layout

| Path | What |
|---|---|
| [`design/boat.toml`](design/boat.toml) | Reference 40 ft sloop: hull, mast, sail plan, motion responses |
| [`design/sea.toml`](design/sea.toml) | Sea states, refraction, visibility |
| [`design/cameras.toml`](design/cameras.toml) | Camera classes: long-zoom PTZ, mid-zoom PTZ (upright and inverted), fixed wide, interior dome, fisheye |
| [`design/electronics.toml`](design/electronics.toml) | Pod kits: SOC, IMU, housing, PoE, network and power budgets |
| [`design/targets.toml`](design/targets.toml) | Target classes and Johnson criteria |
| [`design/rigs/`](design/rigs/) | `gecko5` (pods), `mast5` (1 top + 4 round the mast), `mast5-spreaders`, `whole-boat` |
| [`design/scenarios/`](design/scenarios/) | `coastal-watch` (sea state 4), `mob` (sea state 3), `docking` |
| [`src/osprey/`](src/osprey/) | `frames`, `motion`, `optics`, `stabilize`, `occlusion`, `rig`, `tasking`, `calcs`, `figures`, `render/scene`, `cli` |
| [`runs/`](runs/README.md) | Kept runs, never edited after they are archived |
| [`docs/`](docs/) | [Architecture](docs/architecture.md), [remote runs](docs/remote-simulation.md), README figures |

## Kept runs

| Run | What it shows |
|---|---|
| [`2026-11-06_gecko-sweep`](runs/2026-11-06_gecko-sweep/summary.md) | Every scenario x rig with sector watch; `gecko5` reports in full |
| [`2026-11-06_gecko-docking-render`](runs/2026-11-06_gecko-docking-render/) | 10 s docking render on `gecko5` with optimized aims: video, one frame of `port-down`, all labels |
| [`2026-11-06_pods-fisheye-sweep`](runs/2026-11-06_pods-fisheye-sweep/summary.md) | The dropped design: pods with a down-looking fisheye |
| [`2026-11-06_first-sweep`](runs/2026-11-06_first-sweep/summary.md) | Every scenario x rig before pods: calc reports, figures, looking-group timelines |
| [`2026-11-06_docking-render`](runs/2026-11-06_docking-render/) | 20 s docking render on `mast5-spreaders` |

Source SHAs and hosts are in [runs/README.md](runs/README.md).

<details>
<summary>The earlier single-PTZ rig, rendered</summary>

![The five mast cameras and an overview, rendered in the docking scenario](docs/img/docking-sheet.png)

<sub>`mast5-spreaders` docking render: masthead PTZ looking straight down, forward, port and starboard
spreader cameras, the aft camera under the gooseneck, and an overview.</sub>

</details>

## Phases

0. **Bosun's Chair:** a halyard-hoisted pod with an action camera, IMU and GNSS. It measures the real
   masthead motion that replaces the REF motion model.
1. **Look-down docking:** stereo pairs plus deck registration give a costmap for the pilot.
2. **Spotting:** horizon-band detection, horizon-dip ranging and thermal.
3. **Inspection:** the long-zoom PTZ, cued and slewed to targets.

README figures in `docs/img/` other than the renders and run plots are made from the files in this
repository by [`docs/img/make_readme_figures.py`](docs/img/make_readme_figures.py)
(`uv run python docs/img/make_readme_figures.py`).
