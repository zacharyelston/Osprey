"""Looking groups: which cameras look at what, tick by tick.

Every tick each task (a target to detect, recognize or identify, optionally
with a range precision) gets a looking group of 1 to `max_group` cameras,
highest priority first. A group stops growing once it meets the task's need,
or takes every camera it may if the task asks for group = "max". The rig's
`reserve` cameras are never put in a group: they keep watch, sweeping the
horizon. A camera that changes job is blind while it slews and zooms.

A group is worth more than its best member in three ways:
- resolution: multi-view super-resolution, modest and capped;
- visibility: cameras at different heights see past different wave crests;
- range: two cameras give a triangulation baseline; one camera alone can
  still range by the waterline's dip below the horizon.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from osprey import frames, motion, occlusion, optics, stabilize
from osprey.motion import KN
from osprey.rig import Station, stations

SR_GAIN_PER_VIEW = 0.15   # resolution gain per extra view
SR_GAIN_MAX = 1.4
TRACK_MARGIN_RAD = math.radians(0.5)  # FOV kept around a tracked target
REL_ORIENT_URAD = 50.0    # group cameras calibrated against shared horizon/deck
WATCH_DWELL_S = 0.5


@dataclass
class Task:
    id: str
    cls: str
    kind: object
    pos0: np.ndarray       # world, m
    vel: np.ndarray        # world, m/s
    priority: int
    need: str
    range_frac: float | None
    group: str
    zone: str = "exterior"

    def pos(self, t: float) -> np.ndarray:
        return self.pos0 + self.vel * t


def tasks(p) -> list[Task]:
    hd = p.scenario.heading_deg
    out = []
    for g in p.target:
        tb = math.radians(hd + g.bearing_deg)
        c = math.radians(g.course_deg)
        pos = np.array([g.range_m * math.sin(tb), g.range_m * math.cos(tb), 0.0])
        vel = np.array([math.sin(c), math.cos(c), 0.0]) * g.speed_kn * KN
        out.append(Task(g.id, g.kind, getattr(p.target_class, g.kind), pos, vel, g.priority, g.need,
                        getattr(g, "range_frac", None), getattr(g, "group", "min"),
                        getattr(g, "zone", "exterior")))
    return sorted(out, key=lambda t: t.priority)


@dataclass
class View:
    ok: bool
    d_body: np.ndarray
    range_m: float
    px: float = 0.0        # pixels across the critical dimension, after blur
    p_vis: float = 0.0     # fraction of time not hidden by waves
    dip_sigma: float = math.inf
    cam_world: np.ndarray = field(default_factory=lambda: np.zeros(3))
    focal: float = 0.0
    ifov: float = 0.0


@dataclass
class Quality:
    px: float
    p_vis: float
    range_sigma: float
    met: bool


class Sim:
    def __init__(self, p, rig: str | None = None):
        self.p = p
        sc = p.scenario
        self.dt = sc.dt_s
        self.sts = [s for s in stations(p) if "exterior" in s.zones]
        self.reserve = p.rig.reserve
        self.max_group = p.rig.max_group
        self.occ = occlusion.build(p)
        self.mot = motion.from_scenario(p, dt=0.05)
        self.R = self.mot.R(sc.heading_deg)
        self.res = {}
        self.vel = {}
        self.jit_cov = {}
        for s in self.sts:
            _, v, _, w = self.mot.mount(s.pos, s.on_mast, sc.heading_deg)
            self.res[s.id] = stabilize.residual(w, self.mot.dt, s.cam.stabilization)
            self.vel[s.id] = v
            self.jit_cov[s.id] = np.cov(self.res[s.id].angle.T)
        self.tasks = tasks(p)
        self.k = p.atmosphere.k_refraction
        self.vis_m = sc.visibility_km * 1e3
        self._exposure = {}
        self._vc = {}
        head = frames.heading_to_yaw(sc.heading_deg)
        self.boat_vel = np.array([math.cos(head), math.sin(head), 0.0]) * sc.boat_speed_kn * KN

    def need_px(self, task: Task) -> float:
        return 2 * getattr(self.p.johnson, task.need)

    def exposure(self, h_eye, d, h_t):
        key = (round(h_eye * 2) / 2, round(math.log(max(d, 25.0)) / 0.02), h_t)
        if key not in self._exposure:
            self._exposure[key] = optics.wave_exposure(key[0], math.exp(key[1] * 0.02), h_t, self.p.sea.hs_m,
                                                       self.p.sea.tp_s, k=self.k, n=80)
        return self._exposure[key]

    def view(self, s: Station, task: Task, t: float) -> View:
        key = (s.id, task.id, t)
        if key not in self._vc:
            self._vc[key] = self._view(s, task, t)
        return self._vc[key]

    def _view(self, s: Station, task: Task, t: float) -> View:
        i = min(int(t / self.mot.dt), len(self.mot.t) - 1)
        R = self.R[i]
        boat = self.boat_vel * t + np.array([0, 0, self.mot.heave[i]])
        tgt = task.pos(t) + np.array([0, 0, task.kind.height_m])
        rel = R.T @ (tgt - boat)                     # target top, body frame
        d = rel - s.pos
        rng = float(np.linalg.norm(d))
        u = d / rng
        az, el = frames.az_el(u)
        cam_w = boat + R @ s.pos
        v = View(False, u, rng, cam_world=cam_w)
        if not s.can_point(az, el):
            return v
        if rng > optics.geometric_range_m(cam_w[2], task.kind.height_m, self.k):
            return v
        if rng > optics.contrast_range_m(self.vis_m, task.kind.contrast, self.p.atmosphere.contrast_threshold):
            return v
        if self.occ.blocked(s.pos, rel[None, :])[0]:
            return v
        res = self.res[s.id]
        ang = task.kind.crit_m / rng
        C = self.jit_cov[s.id]
        jit = math.sqrt(max(float(np.trace(C) - u @ C @ u), 0.0))
        fov_need = max(4 * ang, 6 * jit, TRACK_MARGIN_RAD)
        if s.fixed:
            f = s.f_min
        else:
            f_fit = s.cam.width_px * s.cam.pixel_um * 1e-3 / (2 * math.tan(fov_need / 2))
            f = min(max(f_fit, s.f_min), s.f_max)
        ifov = s.ifov(f)
        sl = slice(max(i - 2, 0), i + 3)
        blur = float(np.max(stabilize.across(res.rate[sl], u)) * s.cam.exposure_ms * 1e-3 / ifov
                     + np.max(stabilize.across(self.vel[s.id][sl], u)) / rng * s.cam.exposure_ms * 1e-3 / ifov)
        v.ok = True
        v.focal = f
        v.ifov = ifov
        v.px = task.kind.crit_m / (rng * ifov) / max(1.0, blur)
        v.p_vis = self.exposure(cam_w[2], rng, task.kind.height_m)
        v.dip_sigma = optics.dip_ranging(rng, cam_w[2], ifov, hs=self.p.sea.hs_m, k=self.k)[0]
        return v

    def quality(self, views: list[View], task: Task) -> Quality:
        views = [v for v in views if v.ok]
        if not views:
            return Quality(0.0, 0.0, math.inf, False)
        n = len(views)
        px = max(v.px for v in views) * min(1 + SR_GAIN_PER_VIEW * (n - 1), SR_GAIN_MAX)
        ps = sorted((v.p_vis for v in views), reverse=True)
        p_vis = 1 - (1 - ps[0]) * np.prod([(1 - q) ** 0.5 for q in ps[1:]])
        sig = min(v.dip_sigma for v in views)
        for a in range(n):
            for b in range(a + 1, n):
                va, vb = views[a], views[b]
                base = va.cam_world - vb.cam_world
                u = va.d_body
                perp = float(np.linalg.norm(base - (base @ u) * u))
                ifov = max(va.ifov, vb.ifov)
                sig = min(sig, optics.stereo_sigma_m(va.range_m, perp, ifov, rel_orient_urad=REL_ORIENT_URAD))
        rng = views[0].range_m
        met = px >= self.need_px(task) and p_vis >= 0.5 and (task.range_frac is None or sig / rng <= task.range_frac)
        return Quality(float(px), float(p_vis), float(sig), bool(met))

    def run(self) -> dict:
        sc = self.p.scenario
        ticks = np.arange(0.0, sc.duration_s, self.dt)
        ids = [s.id for s in self.sts]
        state = {s: [] for s in ids}
        prev_job = {s: None for s in ids}
        prev_dir = {s: None for s in ids}
        busy_until = {s: -1.0 for s in ids}
        log = {t.id: [] for t in self.tasks}
        cap = len(self.sts) - self.reserve
        for t in ticks:
            self._vc = {}
            free = list(ids)
            jobs: dict[str, str] = {}
            for task in self.tasks:
                if len(ids) - len(free) >= cap:
                    break
                views = {s.id: self.view(s, task, t) for s in self.sts if s.id in free}
                cands = [sid for sid, v in views.items() if v.ok]
                score = {sid: views[sid].px * views[sid].p_vis * (1.5 if prev_job[sid] == task.id else 1.0)
                         for sid in cands}
                if task.group == "max":
                    cands.sort(key=lambda sid: -score[sid])
                else:
                    # Prefer a camera that meets the need alone and that the
                    # lower-priority tasks need least: the masthead PTZ is
                    # often the only camera that sees over the leeward sails.
                    later = self.tasks[self.tasks.index(task) + 1:]
                    st_by = {s.id: s for s in self.sts}
                    demand = {sid: sum(self.view(st_by[sid], o, t).ok for o in later) for sid in cands}
                    alone = {sid: self.quality([views[sid]], task).met for sid in cands}
                    cands.sort(key=lambda sid: (not alone[sid], demand[sid], -score[sid]))
                group: list[str] = []
                for sid in cands:
                    if len(group) >= self.max_group or len(ids) - len(free) + 1 > cap:
                        break
                    group.append(sid)
                    free.remove(sid)
                    q = self.quality([views[g] for g in group], task)
                    if task.group != "max" and q.met:
                        break
                for sid in group:
                    jobs[sid] = task.id
                live = []
                for sid in group:
                    if prev_job[sid] != task.id:
                        st = next(s for s in self.sts if s.id == sid)
                        ang = math.pi / 2 if prev_dir[sid] is None else math.acos(
                            float(np.clip(prev_dir[sid] @ views[sid].d_body, -1, 1)))
                        busy_until[sid] = t + st.slew_s(ang)
                    if t >= busy_until[sid]:
                        live.append(views[sid])
                    prev_dir[sid] = views[sid].d_body
                q = self.quality(live, task)
                log[task.id].append({"t": float(t), "group": group, "live": len(live), "px": q.px,
                                     "p_vis": q.p_vis, "sigma": q.range_sigma, "met": q.met,
                                     "range": float(np.linalg.norm(task.pos(t) - self.boat_vel * t))})
            for sid in ids:
                j = jobs.get(sid)
                if j is None:
                    state[sid].append("watch")
                    prev_dir[sid] = None
                elif t < busy_until[sid]:
                    state[sid].append(f"slew:{j}")
                else:
                    state[sid].append(j)
                prev_job[sid] = j
        return {"t": ticks, "stations": ids, "state": state, "tasks": log,
                "task_meta": {t.id: {"cls": t.cls, "need": t.need, "priority": t.priority,
                                     "range_frac": t.range_frac, "group": t.group} for t in self.tasks}}


def watch_revisit_s(s: Station, focal_mm: float | None = None) -> float:
    """Seconds for one camera to sweep 360 deg of horizon at a focal length."""
    f = focal_mm or s.f_min
    hf = s.hfov(f)
    steps = math.ceil(2 * math.pi / (0.9 * hf))
    step_s = (0.9 * hf) / math.radians(max(s.cam.slew_dps, 1e-3)) if not s.fixed else 0.0
    return steps * (WATCH_DWELL_S + step_s)


def summary(out: dict) -> dict:
    res = {}
    for tid, rows in out["tasks"].items():
        met = np.array([r["met"] for r in rows])
        gs = np.array([len(r["group"]) for r in rows])
        sig = np.array([r["sigma"] for r in rows])
        rng = np.array([r["range"] for r in rows])
        fin = np.isfinite(sig)
        res[tid] = {"met_frac": float(met.mean()), "group_median": float(np.median(gs)),
                    "group_max": int(gs.max()), "px_median": float(np.median([r["px"] for r in rows])),
                    "sigma_frac_median": float(np.median(sig[fin] / rng[fin])) if fin.any() else math.inf}
    n = len(out["t"])
    st = {}
    for sid, seq in out["state"].items():
        st[sid] = {"watch": seq.count("watch") / n,
                   "slew": sum(x.startswith("slew") for x in seq) / n,
                   "tasked": sum(not x.startswith(("slew", "watch")) for x in seq) / n}
    always_watch = all(any(out["state"][s][i] == "watch" for s in out["stations"]) for i in range(n))
    return {"tasks": res, "stations": st, "always_watch": always_watch}
