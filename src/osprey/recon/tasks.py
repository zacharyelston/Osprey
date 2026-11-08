"""What Recon does once it gets there. A mission's `kind` picks the task:

- search: find a person in the water. An expanding square drifts with the
  datum until the probability of detection (POD) reaches the goal. Re-flown,
  turned and offset, if it ends short.
- survey: scout a site before the boat gets there. An anchorage, a landing
  beach, a reef or an island's wildlife: a lawnmower pattern with the gimbal
  pointing straight down, until the area is imaged. It reports the ground
  sample distance and how many pixels each hazard class gets.
- inspect: look at another vessel from a standoff distance. Orbit it as it
  moves, zoomed in to identify it (the gimbal, or with payload "dual" the
  inboard PTZ eye).
- escort: keep the boat's beams under watch. Circle the boat as it sails, at
  a set radius, for a set time.

Each task sets up what the flight sim needs: its patterns, its search grid
and camera footprints, a progress measure with a goal, and the track length
the sizing loop plans for. spec() hands that to the sim (sim/src/tasks.rs),
which steps the waypoints and the grid; absorb() takes back where it ended.
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


PASSES_MAX = 24                   # search patterns set up for the sim, one per pass


def _polar(range_m: float, bearing_deg: float) -> np.ndarray:
    b = math.radians(bearing_deg)
    return range_m * np.array([math.sin(b), math.cos(b)])


def _sweep_spec(sw: search.Sweep) -> dict:
    return {"along_m": sw.along_m, "p_pass": sw.p_pass, "rects": [list(map(float, r)) for r in sw.footprints()]}


def _grid_spec(g: search.Grid) -> dict:
    return {"x": g.x.ravel().tolist(), "y": g.y.ravel().tolist(), "prior": g.prior.ravel().tolist(),
            "unfound": g.unfound.ravel().tolist(), "datum": g.datum.tolist(), "drift": g.drift.tolist(),
            "nx": int(g.x.shape[1])}


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

    @property
    def progress(self) -> float:
        raise NotImplementedError

    def spec(self) -> dict:
        """What the sim needs to step the task."""
        return {"kind": self.kind, "alt_m": float(self.alt_m), "goal": float(self.goal),
                "drift": [float(x) for x in self.drift]}

    def absorb(self, state: dict):
        """Where the sim left the task."""

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

    def patterns(self) -> list[np.ndarray]:
        """The expanding square for each pass: re-flown turned 45 degrees and offset half a spacing."""
        off = self.plan.spacing_m / 2 * np.array([1.0, 1.0])
        return [self.pattern] + [search.expanding_square(self.plan.spacing_m, self.plan.half_size_m, self.up + 45 * k)
                                 + off for k in range(1, PASSES_MAX)]

    def spec(self):
        # The camera's footprint at every altitude the sim can look from: within 15 m of the search height,
        # to the nearest 5 m.
        keys = sorted({int(round(a / 5) * 5) for a in np.linspace(self.alt_m - 15, self.alt_m + 15, 601)})
        for k in keys:
            if k not in self._sweeps:
                self._sweeps[k] = search.sweep(self.p, k)
        return {**super().spec(), "datum0": self.datum0.tolist(), "spacing": float(self.plan.spacing_m),
                "patterns": [pat.tolist() for pat in self.patterns()],
                "sweeps": {k: _sweep_spec(self._sweeps[k]) for k in keys}, "grid": _grid_spec(self.grid)}

    def absorb(self, state):
        self.wp, self.passes = state["wp"], state["passes"]
        self.pattern = self.patterns()[min(self.passes, PASSES_MAX) - 1]
        self.grid.unfound = np.array(state["unfound"]).reshape(self.grid.unfound.shape)

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
        self.eyes = 2 if getattr(p.payload, "layout", "gimbal") == "dual" else 1
        sw = search.sweep(p, self.alt_m, depression_deg=90.0)
        if self.eyes == 2:
            # Both PTZ eyes turned down and slightly outboard: two footprints side by side.
            sw = replace(sw, half_width_m=2 * sw.half_width_m)
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

    def spec(self):
        return {**super().spec(), "centre": self.centre.tolist(), "pattern": self.pattern.tolist(),
                "sweep": _sweep_spec(self.sweep), "grid": _grid_spec(self.grid)}

    def absorb(self, state):
        self.wp, self.finished = state["wp"], state["finished"]
        self.grid.unfound = np.array(state["unfound"]).reshape(self.grid.unfound.shape)

    @property
    def progress(self):
        return self.grid.pod

    def info(self):
        cam, pl = self.p.camera, self.p.payload
        gsd = self.alt_m * cam.pixel_um * 1e-6 / (pl.search_focal_mm * 1e-3)
        cls = {k: round(getattr(self.p.targets, k).crit_m / gsd, 1) for k in self.p.mission.look_for}
        return {"gsd_cm": gsd * 100, "swath_m": 2 * self.sweep.half_width_m, "track_spacing_m": self.spacing,
                "legs": len(self.pattern) // 2, "px_across": cls,
                "camera": "two side PTZs, turned down" if self.eyes == 2 else "gimbal"}


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

    def where(self, t):
        return self.v0 + self.vel * t

    def spec(self):
        return {**super().spec(), "v0": self.v0.tolist(), "vel": self.vel.tolist(), "r": float(self.r),
                "laps": float(self.laps)}

    def absorb(self, state):
        self.swept, self.theta = state["swept"], state["theta"]

    @property
    def progress(self):
        return min(self.swept / (2 * math.pi * self.laps), 1.0)

    def info(self):
        kind = getattr(self.p.targets, self.p.mission.vessel_class)
        cam = self.p.camera
        slant = math.hypot(self.r, self.alt_m - kind.height_m / 2)
        need = getattr(self.p.johnson, self.p.mission.need)
        f_req = 2 * need * slant * cam.pixel_um * 1e-3 / kind.crit_m          # mm
        f_use = min(max(f_req, cam.focal_mm[0]), cam.focal_mm[1])
        px = kind.crit_m / (slant * optics.ifov(cam.pixel_um, f_use))
        return {"standoff_m": self.r, "slant_m": slant, "focal_needed_mm": f_req, "focal_max_mm": cam.focal_mm[1],
                "px_across_at_focal": px, "resolves": f_req <= cam.focal_mm[1],
                "camera": "inboard PTZ eye" if getattr(self.p.payload, "layout", "gimbal") == "dual" else "gimbal"}


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
        self.swept, self.theta = 0.0, None

    def spec(self):
        return {**Task.spec(self), "v0": self.v0.tolist(), "vel": self.vel.tolist(), "r": float(self.r),
                "duration": float(self.duration)}

    def absorb(self, state):
        self.swept, self.theta, self.t_on, self.t_now = state["swept"], state["theta"], state["t_on"], state["t_now"]

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
