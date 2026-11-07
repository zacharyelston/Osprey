"""What Recon does once it gets there. A mission's `kind` picks the task:

- search: find a person in the water. An expanding square drifts with the
  datum until the probability of detection (POD) reaches the goal. Re-flown,
  turned and offset, if it ends short.
- survey: scout a site before the boat gets there. An anchorage, a landing
  beach, a reef or an island's wildlife: a lawnmower pattern with the gimbal
  pointing straight down, until the area is imaged. It reports the ground
  sample distance and how many pixels each hazard class gets.
- inspect: look at another vessel from a standoff distance. With the gimbal,
  orbit it as it moves, zoomed in to identify it. With fixed fore/aft
  cameras (payload "dual"), make passes beside it, with the vessel ahead and
  then astern, until it has been in view long enough.
- escort: keep the boat's beams under watch. Circle the boat as it sails, at
  a set radius, for a set time.

Each task gives the flight sim a place to fly to, a moving waypoint, a
progress measure with a goal, and the track length the sizing loop plans for.
Positions are world x east, y north, metres, with the boat at the origin at
launch.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from osprey import optics
from osprey.motion import KN
from osprey.recon import search


def _polar(range_m: float, bearing_deg: float) -> np.ndarray:
    b = math.radians(bearing_deg)
    return range_m * np.array([math.sin(b), math.cos(b)])


class Task:
    kind = ""
    progress_label = ""
    alt_m = 0.0
    goal = 1.0
    track_m = 0.0
    drift = np.zeros(2)

    def where(self, t: float) -> np.ndarray:
        """The task's centre at time t: where the boat heads, if it heads anywhere."""
        raise NotImplementedError

    def entry(self, t: float, pos: np.ndarray) -> np.ndarray:
        return self.where(t)

    def target(self, t: float, pos: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def look(self, pos, track_rad, t, dt, v_ground, alt):
        pass

    @property
    def progress(self) -> float:
        raise NotImplementedError

    def done(self) -> str | None:
        return "goal" if self.progress >= self.goal else None

    def info(self) -> dict:
        return {}


class SearchTask(Task):
    kind = "search"
    progress_label = "POD"

    def __init__(self, p, wind: np.ndarray):
        m = p.mission
        self.p = p
        self.alt_m = m.search_alt_m
        self.goal = m.search_pod
        self.drift = np.array(m.drift_ms, float)
        self.datum0 = _polar(m.datum_range_m, m.datum_bearing_deg)
        self.sweep = search.sweep(p, self.alt_m)
        self.plan = search.plan(self.sweep, m.datum_sigma_m, m.search_pod)
        self.track_m = self.plan.track_m
        self.up = math.degrees(math.atan2(-wind[0], -wind[1]))      # first leg into the wind
        self.pattern = search.expanding_square(self.plan.spacing_m, self.plan.half_size_m, self.up)
        self.grid = search.Grid(self.datum0, self.drift, m.datum_sigma_m)
        self.wp, self.passes = 1, 1
        self._sweeps: dict[int, search.Sweep] = {}

    def where(self, t):
        return self.datum0 + self.drift * t

    def target(self, t, pos):
        tgt = self.where(t) + self.pattern[self.wp]
        if np.linalg.norm(tgt - pos) < max(15.0, 0.6 * self.plan.spacing_m):
            self.wp += 1
            if self.wp >= len(self.pattern):
                off = self.plan.spacing_m / 2 * np.array([1.0, 1.0])
                self.pattern = search.expanding_square(self.plan.spacing_m, self.plan.half_size_m,
                                                       self.up + 45 * self.passes) + off
                self.passes += 1
                self.wp = 1
            tgt = self.where(t) + self.pattern[self.wp]
        return tgt

    def look(self, pos, track_rad, t, dt, v_ground, alt):
        key = int(round(alt / 5) * 5)
        if key not in self._sweeps:
            self._sweeps[key] = search.sweep(self.p, key)
        self.grid.look(pos, track_rad, t, dt, v_ground, self._sweeps[key])

    @property
    def progress(self):
        return self.grid.pod

    def info(self):
        return {"sweep_width_eff_m": self.sweep.width_eff_m, "track_spacing_m": self.plan.spacing_m,
                "search_half_size_m": self.plan.half_size_m, "passes": self.passes, "planned": self.plan.pod}


class SurveyTask(Task):
    kind = "survey"
    progress_label = "area imaged"

    def __init__(self, p, wind: np.ndarray):
        m = p.mission
        self.p = p
        self.alt_m = m.survey_alt_m
        self.goal = m.coverage_goal
        self.centre = _polar(m.site_range_m, m.site_bearing_deg)
        self.size = np.array(m.site_size_m, float)                  # across the legs, along the legs
        h = math.radians(m.survey_heading_deg)
        self.along = np.array([math.sin(h), math.cos(h)])
        self.across = np.array([self.along[1], -self.along[0]])
        self.belly = getattr(p.payload, "layout", "gimbal") == "dual" and p.belly is not None
        if self.belly:
            # The belly fisheye, straight down: a wide cone, coarse pixels.
            half = self.alt_m * math.tan(math.radians(p.payload.belly_halfangle_deg))
            sw = search.Sweep(self.alt_m, half, -half, half, math.inf, "fisheye cone", 1.0, 0.999)
        else:
            sw = search.sweep(p, self.alt_m, depression_deg=90.0)
        self.sweep = replace(sw, p_pass=0.999)                       # imaged is imaged
        self.spacing = 2 * sw.half_width_m * (1 - m.sidelap)
        n = max(int(math.ceil(self.size[0] / self.spacing)) + 1, 2)
        offs = (np.arange(n) - (n - 1) / 2) * self.spacing
        run = self.size[1] / 2 + m.overshoot_m
        pts = []
        for i, o in enumerate(offs):
            ends = (-run, run) if i % 2 == 0 else (run, -run)
            pts += [self.centre + o * self.across + e * self.along for e in ends]
        self.pattern = np.array(pts)
        self.track_m = float(np.linalg.norm(np.diff(self.pattern, axis=0), axis=1).sum())
        ext = float(max(self.size)) / 2
        self.grid = search.Grid(self.centre, np.zeros(2), ext / 4.0, cell_m=max(ext / 60, 4.0))
        rel = np.stack([self.grid.x, self.grid.y], -1)
        inside = (np.abs(rel @ self.across) <= self.size[0] / 2) & (np.abs(rel @ self.along) <= self.size[1] / 2)
        self.grid.prior = inside / inside.sum()
        self.wp = 0
        self.finished = False

    def where(self, t):
        return self.centre

    def entry(self, t, pos):
        return self.pattern[0]

    def target(self, t, pos):
        if np.linalg.norm(self.pattern[self.wp] - pos) < 25.0:
            if self.wp + 1 < len(self.pattern):
                self.wp += 1
            else:
                self.finished = True
        return self.pattern[self.wp]

    def look(self, pos, track_rad, t, dt, v_ground, alt):
        if abs(alt - self.alt_m) < 15:
            self.grid.look(pos, track_rad, t, dt, v_ground, self.sweep)

    @property
    def progress(self):
        return self.grid.pod

    def done(self):
        if self.progress >= self.goal:
            return "goal"
        return "pattern" if self.finished else None

    def info(self):
        cam, pl = self.p.camera, self.p.payload
        if self.belly:
            cam = self.p.belly
            gsd = self.alt_m * cam.pixel_um * 1e-6 / (cam.focal_mm[0] * 1e-3)
        else:
            gsd = self.alt_m * cam.pixel_um * 1e-6 / (pl.search_focal_mm * 1e-3)
        cls = {k: round(getattr(self.p.targets, k).crit_m / gsd, 1) for k in self.p.mission.look_for}
        return {"gsd_cm": gsd * 100, "swath_m": 2 * self.sweep.half_width_m, "track_spacing_m": self.spacing,
                "legs": len(self.pattern) // 2, "px_across": cls, "camera": "belly fisheye" if self.belly else "gimbal"}


class InspectTask(Task):
    kind = "inspect"
    progress_label = "orbit done"

    def __init__(self, p, wind: np.ndarray):
        m = p.mission
        self.p = p
        self.alt_m = m.inspect_alt_m
        self.goal = 1.0
        self.v0 = _polar(m.vessel_range_m, m.vessel_bearing_deg)
        c = math.radians(m.vessel_course_deg)
        self.vel = m.vessel_speed_kn * KN * np.array([math.sin(c), math.cos(c)])
        self.r = m.standoff_m
        self.laps = m.laps
        self.track_m = 2 * math.pi * self.r * self.laps
        self.swept = 0.0
        self.theta = None
        self.fixed = getattr(p.payload, "layout", "gimbal") == "dual"
        if self.fixed:
            # Passes beside the vessel: 3 standoffs before it to 3 after, alternating sides.
            self.dwell = m.dwell_s
            self.seen = 0.0
            self.leg = 0
            self.L = 3 * self.r
            self.track_m = self.dwell * 18.0 * 2.5         # nominal: in view about 40 % of the time
            self.hfov = optics.fov(p.camera.width_px, p.camera.pixel_um, p.camera.focal_mm[0])

    def where(self, t):
        return self.v0 + self.vel * t

    def entry(self, t, pos):
        if self.fixed:
            return self._pass_point(t, 0)
        d = pos - self.where(t)
        return self.where(t) + self.r * d / max(np.linalg.norm(d), 1e-6)

    def _pass_point(self, t, k):
        """Start (even k) or end (odd k) of pass k // 2: along the vessel's course,
        offset to one side, the sides and directions alternating."""
        sp = np.linalg.norm(self.vel)
        u = self.vel / sp if sp > 0 else np.array([0.0, 1.0])
        n = np.array([u[1], -u[0]])
        p_ = k // 2
        side = 1 if p_ % 2 == 0 else -1
        start_first = p_ % 2 == 0
        along = -self.L if (k % 2 == 0) == start_first else self.L
        return self.where(t) + along * u + side * self.r * n

    def look(self, pos, track_rad, t, dt, v_ground, alt):
        if not self.fixed:
            return
        d = self.where(t) - pos
        rel = (math.atan2(d[0], d[1]) - track_rad + math.pi) % (2 * math.pi) - math.pi
        slant = math.hypot(np.linalg.norm(d), alt)
        in_view = min(abs(rel), math.pi - abs(rel)) <= self.hfov / 2
        kind = getattr(self.p.targets, self.p.mission.vessel_class)
        px = kind.crit_m / (slant * optics.ifov(self.p.camera.pixel_um, self.p.camera.focal_mm[0]))
        if in_view and px >= 2 * getattr(self.p.johnson, self.p.mission.need):
            self.seen += dt

    def target(self, t, pos):
        if self.fixed:
            tgt = self._pass_point(t, self.leg)
            if np.linalg.norm(tgt - pos) < 40.0:
                self.leg += 1
                tgt = self._pass_point(t, self.leg)
            return tgt
        d = pos - self.where(t)
        th = math.atan2(d[1], d[0])
        if self.theta is not None:
            self.swept += abs((th - self.theta + math.pi) % (2 * math.pi) - math.pi)
        self.theta = th
        ahead = th + 0.5                                             # carrot 0.5 rad round the circle
        return self.where(t) + self.r * np.array([math.cos(ahead), math.sin(ahead)])

    @property
    def progress(self):
        if self.fixed:
            return min(self.seen / self.dwell, 1.0)
        return min(self.swept / (2 * math.pi * self.laps), 1.0)

    def info(self):
        kind = getattr(self.p.targets, self.p.mission.vessel_class)
        if self.fixed:
            slant = math.hypot(self.r, self.alt_m)
            px = kind.crit_m / (slant * optics.ifov(self.p.camera.pixel_um, self.p.camera.focal_mm[0]))
            return {"standoff_m": self.r, "slant_m": slant, "focal_needed_mm": self.p.camera.focal_mm[0],
                    "focal_max_mm": self.p.camera.focal_mm[0], "px_across_at_focal": px,
                    "resolves": px >= 2 * getattr(self.p.johnson, self.p.mission.need),
                    "passes": self.leg // 2, "in_view_s": self.seen, "camera": "fixed fore/aft"}
        cam = self.p.camera
        slant = math.hypot(self.r, self.alt_m - kind.height_m / 2)
        need = getattr(self.p.johnson, self.p.mission.need)
        f_req = 2 * need * slant * cam.pixel_um * 1e-3 / kind.crit_m          # mm
        f_use = min(max(f_req, cam.focal_mm[0]), cam.focal_mm[1])
        px = kind.crit_m / (slant * optics.ifov(cam.pixel_um, f_use))
        return {"standoff_m": self.r, "slant_m": slant, "focal_needed_mm": f_req, "focal_max_mm": cam.focal_mm[1],
                "px_across_at_focal": px, "resolves": f_req <= cam.focal_mm[1], "camera": "gimbal"}


class EscortTask(InspectTask):
    """Circle our own boat as it sails, at a set radius, for a set time: the
    beams that fore/aft cameras on the mast leave to the bird."""
    kind = "escort"
    progress_label = "time on station"

    def __init__(self, p, wind: np.ndarray):
        m = p.mission
        self.p = p
        self.alt_m = m.escort_alt_m
        self.goal = 1.0
        self.v0 = np.zeros(2)
        hb = math.radians(m.boat_heading_deg)
        self.vel = m.boat_speed_kn * KN * np.array([math.sin(hb), math.cos(hb)])
        self.r = m.escort_radius_m
        self.duration = m.escort_min * 60.0
        self.track_m = self.duration * 18.0
        self.t_on = None
        self.t_now = 0.0
        self.swept, self.theta, self.fixed = 0.0, None, False

    def target(self, t, pos):
        if self.t_on is None:
            self.t_on = t
        self.t_now = t
        return super().target(t, pos)

    @property
    def progress(self):
        return 0.0 if self.t_on is None else min((self.t_now - self.t_on) / self.duration, 1.0)

    def info(self):
        kind = getattr(self.p.targets, self.p.mission.watch_for)
        ifov = optics.ifov(self.p.camera.pixel_um, self.p.payload.search_focal_mm)
        reach = min(optics.johnson_range_m(kind.crit_m, ifov, self.p.johnson.detect),
                    optics.contrast_range_m(self.p.mission.visibility_km * 1e3, kind.contrast,
                                            self.p.atmosphere.contrast_threshold))
        return {"escort_radius_m": self.r, "escort_min": self.duration / 60, "watch_for": self.p.mission.watch_for,
                "beam_reach_km": (self.r + reach) / 1e3}


def build(p, wind: np.ndarray) -> Task:
    kind = getattr(p.mission, "kind", "search")
    return {"search": SearchTask, "survey": SurveyTask, "inspect": InspectTask, "escort": EscortTask}[kind](p, wind)
