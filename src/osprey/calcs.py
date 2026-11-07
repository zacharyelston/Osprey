"""Screening checks for one scenario: PASS / WARN / FAIL / INFO rows, eOx style.

Groups: motion at the mounts, stabilization (blur and jitter), reach (how far
each target class is detected), ranging, horizon coverage past the mast and
sails, mass aloft, docking (look-down coverage and stereo depth), and for
rigs built from pods: pod power, network, and timing and attitude.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey import frames, motion, occlusion, optics, stabilize
from osprey.rig import Pod, Station, mass_aloft, pods, stations
from osprey.tasking import REL_ORIENT_URAD

DECK_EYE_M = 2.5          # a person standing in the cockpit, for comparison
MASS_EQ_WARN_KG = 4.0     # masthead-equivalent camera mass, REF budget
MASS_EQ_FAIL_KG = 8.0


@dataclass
class Check:
    group: str
    name: str
    value: str
    limit: str
    status: str
    note: str = ""

    def row(self):
        return (self.status, self.group, self.name, self.value, self.limit, self.note)


def _grade(v: float, ok: float, warn: float, higher_is_better: bool = False) -> str:
    if higher_is_better:
        return "PASS" if v >= ok else "WARN" if v >= warn else "FAIL"
    return "PASS" if v <= ok else "WARN" if v <= warn else "FAIL"


def _horizon_dirs(n: int = 8) -> list[np.ndarray]:
    return [frames.direction(a, 0.0) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def detection_reach(s: Station, kind, p, *, h_eye: float | None = None, focal_mm: float | None = None,
                    blur: float = 1.0) -> tuple[float, str]:
    """Farthest range at which this station detects the class with p_vis >= 0.5,
    and which limit binds there."""
    k = p.atmosphere.k_refraction
    h = h_eye if h_eye is not None else s.pos[2]
    ifov = s.ifov(focal_mm)
    limits = {
        "resolution": optics.johnson_range_m(kind.crit_m, ifov, p.johnson.detect) / max(blur, 1.0),
        "horizon": optics.geometric_range_m(h, kind.height_m, k),
        "atmosphere": optics.contrast_range_m(p.scenario.visibility_km * 1e3, kind.contrast,
                                              p.atmosphere.contrast_threshold),
    }
    d_max = min(limits.values())
    binding = min(limits, key=limits.get)
    if p.sea.hs_m > 0:
        lo, hi = 10.0, d_max
        if optics.wave_exposure(h, hi, kind.height_m, p.sea.hs_m, p.sea.tp_s, k=k, n=120) < 0.5:
            for _ in range(14):
                mid = math.sqrt(lo * hi)
                if optics.wave_exposure(h, mid, kind.height_m, p.sea.hs_m, p.sea.tp_s, k=k, n=120) >= 0.5:
                    lo = mid
                else:
                    hi = mid
            d_max, binding = lo, "waves"
    return d_max, binding


def coverage(p, sts: list[Station], occ, *, range_m: float = 2000.0, h_target: float = 2.0,
             step_deg: float = 1.0) -> tuple[float, np.ndarray]:
    """Fraction of horizon azimuths (body frame, level) seen by at least one
    station, and the per-station visibility mask (n_st, n_az)."""
    az = np.radians(np.arange(0, 360, step_deg))
    pts = np.stack([range_m * np.cos(az), range_m * np.sin(az), np.full_like(az, h_target)], -1)
    mask = np.zeros((len(sts), az.size), bool)
    for i, s in enumerate(sts):
        d = pts - s.pos
        a, e = frames.az_el(d)
        mask[i] = s.can_point(a, e) & ~occ.blocked(s.pos, pts, hull=False)
    return float(mask.any(0).mean()), mask


def dock_band(p, step_m: float = 0.5) -> np.ndarray:
    """Water points (z = 0) in a band of width dock_band_m around the hull."""
    occ = occlusion.build(p, sail="down")
    b = p.boat
    band = p.requirement.dock_band_m
    xs = np.arange(b.stern_x_m - band, b.bow_x_m + band + 1e-9, step_m)
    ys = np.arange(-(b.beam_m / 2 + band), b.beam_m / 2 + band + 1e-9, step_m)
    X, Y = np.meshgrid(xs, ys)
    pts = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], -1)
    hw = occ.half_beam(pts[:, 0])
    outside = np.abs(pts[:, 1]) > hw + 0.05
    near = np.abs(pts[:, 1]) <= np.maximum(hw, 0) + band
    near &= (pts[:, 0] >= b.stern_x_m - band) & (pts[:, 0] <= b.bow_x_m + band)
    return pts[outside & near]


def in_fov(s: Station, aim_body: np.ndarray, focal_mm: float, pts: np.ndarray) -> np.ndarray:
    d = pts - s.pos
    if s.fisheye:
        axis = (aim_body - s.pos) / np.linalg.norm(aim_body - s.pos)
        return (d @ axis) / np.linalg.norm(d, axis=1) >= math.cos(s.hfov() / 2)
    F = frames.look_frame(aim_body - s.pos)
    x, y, z = d @ F[:, 0], d @ F[:, 1], -(d @ F[:, 2])
    hf, vf = s.hfov(focal_mm) / 2, s.vfov(focal_mm) / 2
    return (z > 0) & (np.abs(np.arctan2(x, z)) <= hf) & (np.abs(np.arctan2(y, z)) <= vf)


def optimize_aims(p, sts: list[Station], rounds: int = 3) -> tuple[dict, dict]:
    """Coordinate descent over each PTZ's aim point (on the water) and zoom to
    maximize the fraction of the docking band seen by two or more cameras.
    Fixed cameras keep their mount direction. A PTZ that adds nothing is sent
    back to watch the horizon (its aim is then far out, at its own height)."""
    occ = occlusion.build(p, sail="down")
    pts = dock_band(p)
    b = p.boat
    clear = {s.id: ~occ.blocked(s.pos, pts) for s in sts}
    seen = {}
    for s in sts:
        if s.fixed:
            seen[s.id] = in_fov(s, s.pos + s.boresight, s.f_min, pts) & clear[s.id]
    movable = [s for s in sts if not s.fixed]
    xs = np.arange(b.stern_x_m - 3, b.bow_x_m + 3.1, 1.0)
    ys = np.arange(-5.0, 5.1, 1.0)
    cand = [np.array([x, y, 0.0]) for x in xs for y in ys]
    aims = {s.id: np.array(getattr(p.render.aim, s.id, [0, 0, 0]), float) for s in movable}
    focals = {s.id: float(getattr(p.render.focal_mm, s.id, s.f_min)) for s in movable}
    masks = {s.id: in_fov(s, aims[s.id], focals[s.id], pts) & clear[s.id] for s in movable}

    def score(m):
        return float((np.sum(list(m.values()) + list(seen.values()), axis=0) >= 2).mean())

    for _ in range(rounds):
        for s in movable:
            best = (score(masks), aims[s.id], focals[s.id], masks[s.id])
            for f in (s.f_min, s.f_min * 1.5):
                for a in cand:
                    m = in_fov(s, a, f, pts) & clear[s.id]
                    trial = {**masks, s.id: m}
                    sc = score(trial)
                    if sc > best[0] + 1e-9:
                        best = (sc, a, f, m)
            _, aims[s.id], focals[s.id], masks[s.id] = best
    for s in sorted(movable, key=lambda s: masks[s.id].sum()):
        trial = {**masks, s.id: np.zeros_like(masks[s.id])}
        if score(trial) >= score(masks) - 1e-9:   # adds nothing to docking: keep watch on the horizon
            masks = trial
            aims[s.id] = s.pos + frames.direction(s.face_az, 0.0) * 1000
            focals[s.id] = s.f_min
    return {k: v.tolist() for k, v in aims.items()}, focals


def docking(p, sts: list[Station], aims: dict | None = None, focals: dict | None = None) -> dict:
    occ = occlusion.build(p, sail="down")
    pts = dock_band(p)
    aims = aims if aims is not None else vars(p.render.aim)
    focals = dict(focals if focals is not None else vars(p.render.focal_mm))
    seen = {}
    for s in sts:
        if s.id in aims:
            aim, f = np.array(aims[s.id], float), focals.get(s.id, s.f_min)
        elif s.fixed:
            aim, f = s.pos + s.boresight, s.f_min
        else:
            continue
        seen[s.id] = in_fov(s, aim, f, pts) & ~occ.blocked(s.pos, pts)
        focals.setdefault(s.id, f)
    ids = list(seen)
    count = np.sum([seen[i] for i in ids], axis=0)
    by = {s.id: s for s in sts}
    sig = np.full(len(pts), np.inf)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            ia, ib = ids[a], ids[b]
            both = seen[ia] & seen[ib]
            if not both.any():
                continue
            sa, sb = by[ia], by[ib]
            ifov = max(sa.ifov(focals.get(ia, sa.f_min)), sb.ifov(focals.get(ib, sb.f_min)))
            mid = (sa.pos + sb.pos) / 2
            u = pts[both] - mid
            rng = np.linalg.norm(u, axis=1)
            u = u / rng[:, None]
            base = sa.pos - sb.pos
            perp = np.linalg.norm(base[None, :] - (u @ base)[:, None] * u, axis=1)
            s_ab = np.array([optics.stereo_sigma_m(r, q, ifov) for r, q in zip(rng, perp)])
            sig[both] = np.minimum(sig[both], s_ab)
    edge = np.abs(np.abs(pts[:, 1]) - occ.half_beam(pts[:, 0])) <= 0.75
    return {"pts": pts, "count": count, "sigma": sig, "edge": edge, "seen": seen}


def run(p) -> list[Check]:
    sc, req = p.scenario, p.requirement
    every = stations(p)
    sts = [s for s in every if "exterior" in s.zones]
    near = [s for s in every if "near" in s.zones and "exterior" not in s.zones]
    occ = occlusion.build(p)
    mot = motion.from_scenario(p, duration_s=min(sc.duration_s, 600), dt=0.02)
    k = p.atmosphere.k_refraction
    checks: list[Check] = []
    add = checks.append

    # Motion
    G = "Motion"
    dyn = mot.roll - math.radians(sc.heel_deg)
    add(Check(G, f"Roll about the {sc.heel_deg:.0f} deg heel, rms / max",
              f"{math.degrees(motion.stats(dyn)['rms']):.1f} / {math.degrees(motion.stats(dyn)['max']):.1f} deg", "",
              "INFO", f"{p.sea.state}, Hs {p.sea.hs_m} m, Tp {p.sea.tp_s} s, waves {sc.wave_rel_deg:.0f} deg off the bow"))
    add(Check(G, "Pitch rms / max", f"{math.degrees(motion.stats(mot.pitch)['rms']):.1f} / "
              f"{math.degrees(motion.stats(mot.pitch)['max']):.1f} deg", "", "INFO"))
    res = {}
    for s in sts + near:
        _, v, a, w = mot.mount(s.pos, s.on_mast, sc.heading_deg)
        res[s.id] = (stabilize.residual(w, mot.dt, s.cam.stabilization), v, a, w)
    top = max(sts, key=lambda s: s.pos[2])
    _, v, a, w = res[top.id]
    rate = np.linalg.norm(w, axis=1)
    acc = np.linalg.norm(a, axis=1) / 9.81
    add(Check(G, f"Angular rate at the mounts, p95 / max", f"{math.degrees(np.percentile(rate, 95)):.1f} / "
              f"{math.degrees(rate.max()):.1f} deg/s", "", "INFO", "the same for every camera on a rigid hull"))
    add(Check(G, f"Acceleration at {top.id} ({top.pos[2]:.1f} m), p95", f"{np.percentile(acc, 95):.2f} g", "0.5 g",
              _grade(np.percentile(acc, 95), 0.5, 1.0), "sets the mount, connector and gimbal-motor ratings"))
    add(Check(G, f"Speed of {top.id} through the air, p95", f"{np.percentile(np.linalg.norm(v, axis=1), 95):.1f} m/s",
              "", "INFO", "parallax for near targets; adds to apparent wind on the housing"))

    # Stabilization
    G = "Stabilization"
    bmax = req.blur_px_max
    for s in sts:
        r, v, _, _ = res[s.id]
        worst = max(float(np.percentile(stabilize.blur_px(r, d, s.cam.exposure_ms, s.ifov()), 95))
                    for d in _horizon_dirs())
        add(Check(G, f"{s.id}: blur p95 at {s.f_max:.0f} mm, {s.cam.exposure_ms:g} ms", f"{worst:.2f} px",
                  f"{bmax:g} px", _grade(worst, bmax, 2 * bmax), "worst of 8 horizon bearings"))
        jit = max(stabilize.jitter_rad(r, d) for d in _horizon_dirs())
        half = s.hfov(s.f_max) / 2
        add(Check(G, f"{s.id}: pointing jitter rms vs half-FOV at max zoom", f"{jit * 1e6:.0f} urad",
                  f"{half / 3 * 1e6:.0f} urad", _grade(jit, half / 6, half / 3),
                  f"inner stage saturated {r.saturated:.0%} of the time" if s.cam.stabilization.inner_hz else
                  "no fast stage"))

    # Reach
    G = "Reach"
    for cls, need in vars(getattr(req, "detect_m", None) or type("o", (), {})()).items():
        kind = getattr(p.target_class, cls)
        best = max(((detection_reach(s, kind, p), s) for s in sts), key=lambda x: x[0][0])
        (d, why), s = best
        deck = Station("deck", s.cam_key, s.cam, np.array([0, 0, DECK_EYE_M]), 0, False, ())
        d_deck, _ = detection_reach(deck, kind, p)
        add(Check(G, f"Detect {cls.replace('_', ' ')}", f"{d:,.0f} m ({s.id}, {why})", f">= {need:,} m",
                  _grade(d, need, 0.7 * need, higher_is_better=True),
                  f"same camera at deck height ({DECK_EYE_M} m): {d_deck:,.0f} m"))

    # Ranging
    G = "Ranging"
    ifov = top.ifov()
    for d in (1000, 2000, 5000):
        sig, bias = optics.dip_ranging(d, top.pos[2], ifov, hs=p.sea.hs_m, k=k, dk=p.atmosphere.k_uncertainty)
        add(Check(G, f"Horizon-dip range, {top.id}, at {d / 1000:g} km", f"+/- {sig:.0f} m ({sig / d:.1%})", "", "INFO",
                  f"refraction bias {bias:.0f} m for dk = {p.atmosphere.k_uncertainty}"))
    ring = [s for s in sts if s is not top]
    if ring:
        low = min(ring, key=lambda s: s.pos[2])
        base = top.pos[2] - low.pos[2]
        sig = optics.stereo_sigma_m(2000, base, max(ifov, low.ifov()), rel_orient_urad=50)
        add(Check(G, f"Group stereo {top.id}+{low.id}, {base:.1f} m vertical baseline, at 2 km",
                  f"+/- {sig:.0f} m ({sig / 2000:.1%})", "", "INFO",
                  "relative orientation 50 urad from the shared horizon; a flexing rig without it: mrad"))

    # Coverage
    G = "Coverage"
    cov, mask = coverage(p, sts, occ)
    add(Check(G, f"Horizon seen by at least one camera ({sc.sail}, heel {sc.heel_deg:g} deg)", f"{cov:.1%}",
              f">= {req.coverage_min:.0%}", _grade(cov, req.coverage_min, req.coverage_min - 0.05, True)))
    if len(sts) > 1:
        lower = mask[[i for i, s in enumerate(sts) if s is not top]].any(0).mean()
        add(Check(G, f"Horizon seen without {top.id}", f"{lower:.1%}", "", "INFO",
                  "what is left when the masthead PTZ is busy in a group"))
        two = (mask.sum(0) >= 2).mean()
        add(Check(G, "Horizon seen by two or more cameras", f"{two:.1%}", "", "INFO",
                  "where a looking group of 2+ is possible"))
    if any(s.sector < 2 * math.pi - 1e-9 for s in sts):
        az = np.radians(np.arange(0, 360, 1.0))
        sec = mask & np.array([s.in_sector(az) for s in sts])
        one, two = sec.any(0).mean(), (sec.sum(0) >= 2).mean()
        add(Check(G, "Horizon inside a watch sector, unblocked", f"{one:.1%}", f">= {req.coverage_min:.0%}",
                  _grade(one, req.coverage_min, req.coverage_min - 0.05, True), "every bearing has a camera sweeping it"))
        add(Check(G, "Horizon inside two or more watch sectors", f"{two:.1%}", "", "INFO",
                  "overlap: a camera can leave its sector for a group while a neighbour keeps the watch"))

    # Mass aloft
    G = "Mass aloft"
    pds = pods(p)
    m, eq = mass_aloft(every, p.mast.truck_z_m, pds)
    what = "cameras and pod electronics" if pds else "cameras only"
    add(Check(G, "Mass on the mast / masthead equivalent", f"{m:.1f} / {eq:.1f} kg",
              f"{MASS_EQ_WARN_KG:g} kg eq", _grade(eq, MASS_EQ_WARN_KG, MASS_EQ_FAIL_KG),
              f"equivalent = same heeling moment at the truck; {what}, no brackets or cable"))
    if pds:
        _, eq_cams = mass_aloft(every, p.mast.truck_z_m)
        add(Check(G, "Of which pod SOCs, IMUs and housings (masthead equivalent)", f"{eq - eq_cams:.1f} kg", "",
                  "INFO", f"{pds[0].electronics_kg:.2f} kg a pod"))

    # Docking
    if hasattr(req, "dock_band_m"):
        G = "Docking"
        dk = docking(p, sts + near)
        two = float((dk["count"] >= 2).mean())
        add(Check(G, f"Water within {req.dock_band_m:g} m of the hull seen by 2+ cameras", f"{two:.1%}",
                  f">= {req.dock_two_view_min:.0%}", _grade(two, req.dock_two_view_min, req.dock_two_view_min - 0.15, True),
                  f"one or more: {(dk['count'] >= 1).mean():.1%}"))
        e = dk["sigma"][dk["edge"]]
        fin = e[np.isfinite(e)]
        pair = float(np.isfinite(e).mean())
        add(Check(G, "Hull edge (within 0.75 m) with a stereo pair", f"{pair:.1%}",
                  f">= {req.dock_two_view_min:.0%}", _grade(pair, req.dock_two_view_min,
                                                              req.dock_two_view_min - 0.15, True)))
        worst = float(np.percentile(fin, 95)) * 100 if fin.size else math.inf
        add(Check(G, "Stereo depth where the hull edge has a pair, p95", f"{worst:.1f} cm",
                  f"{req.dock_stereo_cm:g} cm", _grade(worst, req.dock_stereo_cm, 2 * req.dock_stereo_cm)))
        aims, focals = optimize_aims(p, sts + near)
        dko = docking(p, sts + near, aims, focals)
        e = dko["sigma"][dko["edge"]]
        add(Check(G, "Same, with aims optimized for two views", f"{(dko['count'] >= 2).mean():.1%}",
                  f">= {req.dock_two_view_min:.0%}", _grade(float((dko['count'] >= 2).mean()), req.dock_two_view_min,
                                                              req.dock_two_view_min - 0.15, True),
                  f"hull edge with a stereo pair: {np.isfinite(e).mean():.0%}, depth p95 "
                  f"{np.percentile(e[np.isfinite(e)], 95) * 100 if np.isfinite(e).any() else math.inf:.1f} cm; aims: " +
                  ", ".join(f"{k} watch" if v[2] > 0 else f"{k} ({v[0]:.0f}, {v[1]:.0f}) @ {focals[k]:.1f} mm"
                            for k, v in aims.items())))
        for s in sts:
            if s.id not in vars(p.render.aim):
                continue
            r, v, _, _ = res[s.id]
            aim = np.array(getattr(p.render.aim, s.id), float) - s.pos
            f = getattr(p.render.focal_mm, s.id, s.f_min)
            b = stabilize.blur_px(r, aim / np.linalg.norm(aim), s.cam.exposure_ms, s.ifov(f), vel=v,
                                  range_m=float(np.linalg.norm(aim)))
            add(Check(G, f"{s.id}: look-down blur p95 incl. parallax", f"{np.percentile(b, 95):.2f} px",
                      f"{bmax:g} px", _grade(float(np.percentile(b, 95)), bmax, 2 * bmax)))
        for s in near:
            r, v, _, _ = res[s.id]
            rng = s.pos[2] / math.cos(math.radians(30))      # the water 30 deg off the nadir
            b = stabilize.blur_px(r, s.boresight, s.cam.exposure_ms, s.ifov(), vel=v, range_m=rng)
            add(Check(G, f"{s.id}: fisheye blur p95 incl. parallax", f"{np.percentile(b, 95):.2f} px",
                      f"{bmax:g} px", _grade(float(np.percentile(b, 95)), bmax, 2 * bmax),
                      f"unstabilized, {s.cam.exposure_ms:g} ms"))
    if pds:
        checks += pod_checks(p, pds, mot, res)
    return checks


def _poe_class(watts: float, poe) -> str | None:
    fits = [(lim, name) for name, lim in vars(poe).items() if lim >= watts]
    return min(fits)[1] if fits else None


def pod_checks(p, pds: list[Pod], mot: motion.Motion, res: dict) -> list[Check]:
    """Power, network, and timing and attitude for a rig built from pods."""
    el = p.electronics
    net, pw = el.network, el.power
    checks: list[Check] = []
    add = checks.append

    G = "Pod power"
    for pd in pds:
        for port, w in pd.ports():
            cls = _poe_class(w, el.poe)
            add(Check(G, f"{port}: peak draw at the PoE port", f"{w:.1f} W", cls or "71.3 W",
                      "PASS" if cls else "FAIL",
                      f"needs {cls}" if cls else "over 802.3bt Type 4: needs a second cable or local power"))
    ptz = [s for pd in pds for s in pd.members if not s.fixed]
    watcher = max(ptz, key=lambda s: s.pos[2]).id if ptz else None
    draw = {mode: sum(pd.load_w(mode, {watcher}) for pd in pds) / pw.pse_efficiency
            for mode in ("watch", "active")}
    add(Check(G, "Whole system from the house bank, watch / active",
              f"{draw['watch'] / pw.house_v:.1f} / {draw['active'] / pw.house_v:.1f} A",
              "", "INFO", f"{draw['watch']:.0f} / {draw['active']:.0f} W at {pw.house_v:g} V; "
                          f"watch = {watcher} working, other PTZs parked"))
    duty = vars(pw.duty_h)
    ah = sum(draw[m] * h for m, h in duty.items()) / pw.house_v
    add(Check(G, "Energy per day underway", f"{ah:.0f} Ah", f"{pw.budget_ah_day:g} Ah",
              _grade(ah, pw.budget_ah_day, 1.5 * pw.budget_ah_day),
              ", ".join(f"{h:g} h {m}" for m, h in duty.items())))

    G = "Pod network"
    rates = {pd.id: pd.pixel_rate(net.fps) for pd in pds}
    bare = [pd for pd in pds if not pd.has_computer]
    if bare:
        add(Check(G, f"{len(bare)} mounts without a pod computer", ", ".join(pd.id for pd in bare), "", "INFO",
                  "each camera encodes itself: detection runs on compressed streams at the pilot computer"))
    smart = [pd for pd in pds if pd.has_computer] or pds
    worst = max(smart, key=lambda pd: rates[pd.id])
    px = rates[worst.id]
    raw = px * net.raw_bits_px / 1e6
    add(Check(G, f"{worst.id}: raw sensor rate vs one gigabit link", f"{raw:,.0f} Mb/s",
              f"{net.link_mbps:,.0f} Mb/s", "INFO",
              f"{raw / net.link_mbps:.1f}x the link: frames must be encoded, and searched, on the pod"))
    enc = px * net.codec_bits_px / 1e6
    usable = net.link_mbps * net.usable_frac
    add(Check(G, f"{worst.id}: encoded streams on its link", f"{enc:.0f} Mb/s", f"{usable:.0f} Mb/s",
              _grade(enc, usable, net.link_mbps), f"H.265 at {net.codec_bits_px:g} bit/px, {net.fps:g} fps"))
    total = sum(rates.values()) * net.codec_bits_px / 1e6
    up = net.uplink_mbps * net.usable_frac
    add(Check(G, "All pods on the switch uplink to the pilot", f"{total:.0f} Mb/s", f"{up:.0f} Mb/s",
              _grade(total, up, net.uplink_mbps)))
    add(Check(G, f"{worst.id}: SOC encoder load", f"{px / 1e6:.0f} Mpx/s", f"{worst.soc.encode_mpx_s:g} Mpx/s",
              _grade(px / 1e6, worst.soc.encode_mpx_s, 1.25 * worst.soc.encode_mpx_s), worst.soc.label))
    need = px / net.fps * net.detect_fps / 1e6 * net.detector_gop_per_mpx / 1e3
    have = worst.soc.tops_int8 * net.npu_utilization
    add(Check(G, f"{worst.id}: detection on full-resolution frames", f"{need:.1f} TOPS", f"{have:.1f} TOPS",
              _grade(need, have, 1.5 * have),
              f"{net.detect_fps:g} fps, {net.detector_gop_per_mpx:g} GOP/Mpx, {net.npu_utilization:.0%} of the NPU"))

    G = "Pod timing"
    top = max(pds, key=lambda pd: pd.pos[2])
    _, _, a, w = res[top.members[0].id]
    rate = float(np.percentile(np.linalg.norm(w, axis=1), 95))
    sync = rate * net.ptp_sync_us * 1e-6
    add(Check(G, "Shutter sync error x mount rate, p95 (PTP)", f"{sync * 1e6:.2f} urad", f"{REL_ORIENT_URAD:g} urad",
              _grade(sync * 1e6, REL_ORIENT_URAD / 5, REL_ORIENT_URAD),
              f"with software timestamps ({net.sw_sync_us:g} us): {rate * net.sw_sync_us:.0f} urad"))
    mast = [pd for pd in pds if pd.on_mast and pd.imu.rate_hz > 0]
    if len(mast) > 1:
        hi, lo = max(mast, key=lambda pd: pd.pos[2]), min(mast, key=lambda pd: pd.pos[2])
        flex = np.abs(mot.flex(hi.pos[2]) - mot.flex(lo.pos[2]))
        diff = float(np.percentile(flex, 95)) * 1e6
        rig_hz = p.motion.rig_mode_hz
        add(Check(G, f"Mast flex between {hi.id} and {lo.id} pods, p95, no IMU", f"{diff:.0f} urad",
                  f"{REL_ORIENT_URAD:g} urad", _grade(diff, REL_ORIENT_URAD, 2 * REL_ORIENT_URAD),
                  f"{rig_hz:g} Hz bending; horizon fixes at {net.horizon_fix_hz:g} Hz cannot follow it"))
        T = 1 / net.horizon_fix_hz
        imu = hi.imu
        drift = math.hypot(math.radians(imu.gyro_arw_deg_rt_h) / 60 * math.sqrt(T),
                           math.radians(imu.gyro_bias_deg_h) / 3600 * T) * math.sqrt(2) * 1e6
        tot = math.hypot(REL_ORIENT_URAD, drift)
        add(Check(G, "Relative orientation with pod gyros between horizon fixes", f"{tot:.0f} urad",
                  f"{2 * REL_ORIENT_URAD:g} urad", _grade(tot, 1.2 * REL_ORIENT_URAD, 2 * REL_ORIENT_URAD),
                  f"{REL_ORIENT_URAD:g} urad horizon fix (+) {drift:.0f} urad gyro drift over {T:g} s, two pods"))
        base = hi.pos[2] - lo.pos[2]
        ifov = max(s.ifov() for s in hi.members + lo.members if not s.fixed)
        no = optics.stereo_sigma_m(2000, base, ifov, rel_orient_urad=REL_ORIENT_URAD + diff)
        yes = optics.stereo_sigma_m(2000, base, ifov, rel_orient_urad=tot)
        add(Check(G, f"Stereo {hi.id}+{lo.id} at 2 km ({base:.1f} m baseline), no IMU / with",
                  f"+/- {no:.0f} / {yes:.0f} m", "", "INFO", "what the pod gyros buy a looking group"))
    checks += pair_checks(p, pds, mot, res, rate)
    f = a + np.array([0.0, 0.0, motion.G])
    tilt = np.degrees(np.arccos(np.clip(f[:, 2] / np.linalg.norm(f, axis=1), -1, 1)))
    roll = np.degrees(np.abs(mot.roll))
    add(Check(G, f"Accelerometer-only tilt error at {top.id}, p95", f"{np.percentile(tilt, 95):.1f} deg",
              "", "INFO", f"specific force vs true vertical (roll p95 {np.percentile(roll, 95):.0f} deg): "
                          "accelerometers alone are not an attitude sensor aloft, the gyros are"))
    return checks


def pair_checks(p, pds: list[Pod], mot: motion.Motion, res: dict, rate: float) -> list[Check]:
    """Stereo pairs across the boat: two horizontal mounts at the same height,
    port and starboard, whose forward (or aft) cameras look the same way."""
    net = p.electronics.network
    checks: list[Check] = []
    add = checks.append
    G = "Pairs"
    horiz = [pd for pd in pds if pd.horizontal]
    for a in horiz:
        for b in horiz:
            if not (a.pos[1] > 0 > b.pos[1] and abs(a.pos[2] - b.pos[2]) < 0.05):
                continue
            base = abs(a.pos[1] - b.pos[1])
            flex = float(np.percentile(np.abs(mot.flex(a.pos[2]) - mot.flex(b.pos[2])), 95)) * 1e6
            cams = [s for s in a.members + b.members]
            ifov = max(s.ifov() for s in cams)
            sw = rate * net.sw_sync_us                                  # urad, frames not taken together
            hw = rate * net.ptp_sync_us
            name = f"{a.id.split('-')[0]} pair ({a.id}+{b.id})"
            add(Check(G, f"{name}: baseline and mast flex between them", f"{base:.2f} m, {flex:.0f} urad", "",
                      "INFO", "same height: the mast's fore-aft bending moves both together"))
            r_sw = math.hypot(REL_ORIENT_URAD, sw)
            r_hw = math.hypot(REL_ORIENT_URAD, hw)
            for d in (30.0, 200.0, 1000.0):
                s_sw = optics.stereo_sigma_m(d, base, ifov, rel_orient_urad=r_sw)
                s_hw = optics.stereo_sigma_m(d, base, ifov, rel_orient_urad=r_hw)
                add(Check(G, f"{name}: stereo range at {d:g} m, camera clocks / hardware sync",
                          f"+/- {s_sw:.2f} / {s_hw:.2f} m", f"{0.05 * d:g} m",
                          _grade(s_sw, 0.02 * d, 0.05 * d),
                          f"{net.sw_sync_us / 1e3:g} ms between frames at {math.degrees(rate):.1f} deg/s costs "
                          f"{sw:.0f} urad; hardware-synced shutters {hw:.1f} urad"))
    return checks
