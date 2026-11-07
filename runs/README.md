# Kept runs

Each directory is a copy of an `out/` run worth keeping, named `<date>_<name>`,
with the source SHA it was made from. Never edit an archived run; make a new
one.

SHAs are as of the 2026-11-06 history rewrite that took internal host names
out of the repository. Reports generated before it still print the old SHA:
0bafbe9 = 47ed25e, db972f1 = 9af2de6, c2ca9a3 = 952d1da, b448b35 = 0f30414,
791985c = 36642dd. Hosts are named gpu1 and gpu2 (see
docs/remote-simulation.md).

| Run | SHA | Host | What it shows |
|---|---|---|---|
| [2026-11-06_first-sweep](2026-11-06_first-sweep/) | 47ed25e | gpu1 | Every scenario x rig: calc reports, figures, looking-group timelines; `summary.md` |
| [2026-11-06_docking-render](2026-11-06_docking-render/) | 9af2de6 | gpu1 (EGL) | Sample of a 20 s docking render on mast5-spreaders: contact-sheet video, one frame's RGB/depth/class, all labels |
| [2026-11-06_pods-fisheye-sweep](2026-11-06_pods-fisheye-sweep/) | 952d1da | gpu1 | Pods with a down-looking fisheye (the dropped design): calc reports for the three scenarios |
| [2026-11-06_gecko-docking-render](2026-11-06_gecko-docking-render/) | 0f30414 | gpu1 (EGL) | Sample of a 10 s docking render on gecko5 with optimized aims: video, one frame of `port-down`, all labels |
| [2026-11-07_recon-cyclone-modes](2026-11-07_recon-cyclone-modes/) | feat/cyclone-spin-only | local | Recon as a Cyclone flown by its four modes (1 lift-off and landing on A, 2 spinning hover, 3 spinning travel, 4 wing-borne with the dihedral wing): every move's guard and cost, launch and recovery charged to the sizing, A alone against A with A2, re-sized for all seven jobs. Supersedes 2026-11-07_recon-cyclone |
| [2026-11-07_recon-cyclone](2026-11-07_recon-cyclone/) | feat/recon-cyclone | local | Recon as a Cyclone: the twin-boom one-birds rebuilt with three wing arms that spin as a rotor, flown as built (stopped wing and tricopter) and re-sized for all seven jobs, against the tailsitter |
| [2026-11-07_recon-water](2026-11-07_recon-water/) | feat/recon-water | local | Recon on the water: every one-bird afloat, take-off from the sea, landing loads; the float kit bolted on, and every airframe and payload re-sized with it aboard; the tailsitter sized, floated upright and launched from the water |
| [2026-11-06_recon-wings](2026-11-06_recon-wings/) | d81f91c | gpu1 | Recon: blended wing and crescent flying wing, both payloads, seven jobs each, capability matrices; anti-piracy awareness; plugs for the blended wings, ladder frames for both flying wings |
| [2026-11-06_recon-payloads](2026-11-06_recon-payloads/) | 7f1236d | local | Recon: seven jobs for each payload (gimbal; a PTZ eye each side plus a belly fisheye), with both capability matrices |
| [2026-11-06_pairs-sweep](2026-11-06_pairs-sweep/) | 70118ad | gpu1 | Every scenario x rig with `spreader-pairs` (dual mounts on the spreader tips) in full |
| [2026-11-06_pairs-docking-render](2026-11-06_pairs-docking-render/) | 70118ad | gpu1 (EGL) | 10 s docking render on `spreader-pairs` with optimized aims |
| [2026-11-06_recon-missions](2026-11-06_recon-missions/) | 7c146a0 | local | Recon as the scout: six jobs (search, survey, inspect), each sized and flown, and the capability matrix |
| [2026-11-06_recon-phase1](2026-11-06_recon-phase1/) | ca12777 | local | Recon phase 1: each mission sized (OpenMDAO), calibrated and flown (3-DOF) |
| [2026-11-06_gecko-sweep](2026-11-06_gecko-sweep/) | 36642dd | gpu1 | Every scenario x rig with sector watch; gecko5 reports in full, mast5 and mast5-spreaders sims for comparison |
