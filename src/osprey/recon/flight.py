"""3-DOF point-mass flight simulation of a Recon mission.

The drone launches from the moving boat, flies to the datum (which drifts
with the water), searches an expanding square laid out in the water's frame,
and returns to the boat. The mission's boat_mode says what the boat does
meanwhile:
- "return": it turns back to the datum and heaves to there, drifting (the
  usual man-overboard drill);
- "sail": it sails on. It flies a point-mass model:
- wind triangle to hold the ground track;
- bank-limited turns with their load factor and induced drag;
- climb limited by excess shaft power;
- an electric energy budget.
It leaves the search for home when POD reaches the goal, the search time runs
out, or the battery reaches the energy to get home plus the reserve ("bingo").
A pattern that ends short of the goal is flown again, turned 45 deg and
offset half a track spacing.

World frame: x east, y north, metres; headings clockwise from north.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey.motion import KN
from osprey.recon import search

G = 9.81
PHASES = ("outbound", "search", "return", "recovered", "lost")


def rho(h: float) -> float:
    """ISA air density at altitude h (m)."""
    return 1.225 * (1 - 2.2558e-5 * h) ** 4.2559


@dataclass
class Aircraft:
    mass_kg: float
    S_m2: float
    span_m: float
    cd0: float             # whole-aircraft zero-lift drag coefficient on S
    k: float               # induced drag factor: CD = cd0 + k CL^2
    cl_max: float
    eta_prop: float
    eta_motor: float
    p_aux_w: float         # avionics and payload
    energy_j: float        # usable battery energy
    p_shaft_max_w: float
    v_search: float
    bank_max_rad: float

    @property
    def W(self) -> float:
        return self.mass_kg * G

    def drag(self, v: float, h: float, n: float = 1.0) -> float:
        q = 0.5 * rho(h) * v * v
        cl = n * self.W / (q * self.S_m2)
        return q * self.S_m2 * (self.cd0 + self.k * cl * cl)

    def power(self, v: float, h: float, n: float = 1.0, climb: float = 0.0) -> float:
        """Electric power (W) to fly at airspeed v, load factor n, climb rate."""
        shaft = max(self.drag(v, h, n) * v + self.W * climb, 0.0) / self.eta_prop
        return shaft / self.eta_motor + self.p_aux_w

    def v_stall(self, h: float, n: float = 1.0) -> float:
        return math.sqrt(2 * n * self.W / (rho(h) * self.S_m2 * self.cl_max))

    def best_range_speed(self, h: float, headwind: float) -> float:
        """Airspeed that minimizes energy per metre over the ground."""
        vs = self.v_stall(h)
        vs_grid = np.linspace(1.2 * vs, 3.5 * vs, 80)
        cost = [self.power(v, h) / max(v - headwind, 0.5) for v in vs_grid]
        return float(vs_grid[int(np.argmin(cost))])

    @classmethod
    def from_design(cls, p, d: dict) -> "Aircraft":
        pr = p.propulsion
        return cls(d["mass_total_kg"], d["S_m2"], d["span_m"], d["cd0"], d["k"], p.wing.cl_max,
                   pr.prop_efficiency, pr.motor_efficiency, p.avionics.power_w + p.camera.power_w[1],
                   d["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable, pr.motor_peak_w,
                   d["v_search_ms"], math.radians(p.limits.bank_max_deg))


def _wind(m) -> np.ndarray:
    """Wind as the vector the air moves along (east, north), m/s."""
    a = math.radians(m.wind_from_deg)
    return -m.wind_kn * KN * np.array([math.sin(a), math.cos(a)])


def _wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def simulate(p, ac: Aircraft, *, dt: float = 0.5, t_max: float = 3 * 3600.0,
             search_time_max: float | None = None) -> dict:
    m = p.mission
    wind = _wind(m)
    drift = np.array(m.drift_ms, float)
    hb = math.radians(m.boat_heading_deg)
    boat_v = m.boat_speed_kn * KN * np.array([math.sin(hb), math.cos(hb)])
    b = math.radians(m.datum_bearing_deg)
    datum0 = m.datum_range_m * np.array([math.sin(b), math.cos(b)])

    sw = search.sweep(p, m.search_alt_m)
    pl = search.plan(sw, m.datum_sigma_m, m.search_pod)
    up = math.degrees(math.atan2(-wind[0], -wind[1]))           # first leg into the wind
    pattern = search.expanding_square(pl.spacing_m, pl.half_size_m, up)
    passes = 1
    t_cap = m.search_time_max_s if search_time_max is None else search_time_max
    grid = search.Grid(datum0, drift, m.datum_sigma_m)

    sweeps: dict[int, search.Sweep] = {}
    speeds: dict[tuple[int, int], float] = {}

    def sweep_at(alt):
        key = int(round(alt / 5) * 5)
        if key not in sweeps:
            sweeps[key] = search.sweep(p, key)
        return sweeps[key]

    def range_speed(alt, headwind):
        key = (int(round(alt / 10)), int(round(headwind * 2)))
        if key not in speeds:
            speeds[key] = ac.best_range_speed(key[0] * 10.0, key[1] / 2)
        return speeds[key]

    boat_mode = getattr(m, "boat_mode", "sail")
    boat_speed = m.boat_speed_kn * KN
    boat = np.zeros(2)
    pos = np.zeros(2)
    h, psi, v = 2.0, math.atan2(datum0[0], datum0[1]), ac.v_search
    energy = ac.energy_j
    phase, wp_i, t_search0 = "outbound", 1, None
    rec = {k: [] for k in ("t", "x", "y", "h", "v", "phase", "energy", "pod", "power", "bank", "boat_x", "boat_y")}
    t = 0.0
    while t < t_max and phase not in ("recovered", "lost"):
        datum = datum0 + drift * t
        if phase == "outbound":
            target, h_cmd = datum, (m.cruise_alt_m if np.linalg.norm(datum - pos) > 600 else m.search_alt_m)
            if np.linalg.norm(datum - pos) < 30:
                phase, t_search0 = "search", t
        if phase == "search":
            target = datum0 + drift * t + pattern[wp_i]
            h_cmd = m.search_alt_m
            if np.linalg.norm(target - pos) < max(15.0, 0.6 * pl.spacing_m):
                wp_i += 1
                if wp_i >= len(pattern) and grid.pod < m.search_pod:
                    off = pl.spacing_m / 2 * np.array([1.0, 1.0])
                    pattern = search.expanding_square(pl.spacing_m, pl.half_size_m, up + 45 * passes) + off
                    passes += 1
                    wp_i = 1
            home = float(np.linalg.norm(boat - pos))
            v_home = range_speed(m.cruise_alt_m, float(np.linalg.norm(wind)))
            away = boat_speed if boat_mode == "sail" else 0.0
            t_home = home / max(v_home - np.linalg.norm(wind) - away, 1.0)   # worst case: all against
            bingo = ac.power(v_home, m.cruise_alt_m) * t_home * (1 + m.reserve_frac)
            if grid.pod >= m.search_pod or t - t_search0 > t_cap or energy <= bingo:
                phase = "return"
                rec.setdefault("why", []).append("pod" if grid.pod >= m.search_pod else "time"
                                                 if t - t_search0 > t_cap else "bingo")
        if phase == "return":
            target = boat
            h_cmd = m.cruise_alt_m if np.linalg.norm(boat - pos) > 400 else 15.0
            if np.linalg.norm(boat - pos) < m.recovery_radius_m:
                phase = "recovered"
                continue

        # Speed: search speed in the search, best range for the wind otherwise.
        to = target - pos
        dist = float(np.linalg.norm(to))
        course = math.atan2(to[0], to[1]) if dist > 1e-6 else psi
        u = np.array([math.sin(course), math.cos(course)])
        head = -float(wind @ u)
        v = ac.v_search if phase == "search" else range_speed(h, head)
        # Wind triangle: air heading that makes good the course. `cross` is the
        # wind's push to the right of the course; crab left into it.
        cross = float(wind @ np.array([u[1], -u[0]]))
        psi_d = course - math.asin(max(-1.0, min(1.0, cross / v)))
        rate_max = G * math.tan(ac.bank_max_rad) / v
        dpsi = max(-rate_max * dt, min(rate_max * dt, _wrap(psi_d - psi)))
        psi = _wrap(psi + dpsi)
        bank = math.atan(v * (dpsi / dt) / G)
        n = 1 / math.cos(bank)
        climb_max = max((ac.p_shaft_max_w * ac.eta_prop - ac.drag(v, h, n) * v) / ac.W, 0.0)
        climb = max(-3.0, min(climb_max, (h_cmd - h) / 8.0))
        pw = ac.power(v, h, n, climb)
        vg = v * np.array([math.sin(psi), math.cos(psi)]) + wind
        if phase == "search" and abs(h - m.search_alt_m) < 15:
            grid.look(pos, math.atan2(vg[0], vg[1]), t, dt, float(np.linalg.norm(vg)), sweep_at(h))
        for k_, v_ in (("t", t), ("x", pos[0]), ("y", pos[1]), ("h", h), ("v", v), ("phase", phase),
                       ("energy", energy), ("pod", grid.pod), ("power", pw), ("bank", bank),
                       ("boat_x", boat[0]), ("boat_y", boat[1])):
            rec[k_].append(v_)
        pos = pos + vg * dt
        h = max(h + climb * dt, 0.0)
        if boat_mode == "return" and np.linalg.norm(datum - boat) > 150:
            boat = boat + boat_speed * (datum - boat) / np.linalg.norm(datum - boat) * dt
        elif boat_mode == "return":
            boat = boat + drift * dt                       # hove to, drifting with the person
        else:
            boat = boat + boat_v * dt
        energy -= pw * dt
        if energy <= 0:
            phase = "lost"
        t += dt

    out = {k: np.array(v_) for k, v_ in rec.items() if k != "why"}
    out.update(grid=grid, sweep=sw, plan=pl, pattern=pattern, datum0=datum0, drift=drift, wind=wind,
               outcome=phase, why=(rec.get("why") or ["-"])[0], passes=passes)
    return out


def summary(p, ac: Aircraft, r: dict) -> dict:
    ph = r["phase"]
    t = r["t"]
    pod = r["pod"]

    def first(mask):
        i = np.flatnonzero(mask)
        return float(t[i[0]]) if i.size else math.inf

    on_scene = first(ph == "search")
    left = first(ph == "return")
    seg = np.hypot(np.diff(r["x"]), np.diff(r["y"]))
    return {
        "outcome": r["outcome"],
        "left_search_because": r["why"],
        "flight_time_s": float(t[-1]) if t.size else 0.0,
        "on_scene_s": on_scene,
        "search_s": (left - on_scene) if math.isfinite(left) else math.inf,
        "pod": float(pod[-1]) if pod.size else 0.0,
        "pod_planned": r["plan"].pod,
        "t_pod50_s": first(pod >= 0.5),
        "t_pod90_s": first(pod >= 0.9),
        "distance_km": float(seg.sum() / 1e3),
        "energy_left_frac": float(r["energy"][-1] / ac.energy_j) if t.size else 0.0,
        "bank_max_deg": float(np.degrees(np.abs(r["bank"]).max())) if t.size else 0.0,
        "power_mean_w": float(np.mean(r["power"])) if t.size else 0.0,
        "sweep_width_eff_m": r["sweep"].width_eff_m,
        "track_spacing_m": r["plan"].spacing_m,
        "search_half_size_m": r["plan"].half_size_m,
        "search_passes": r["passes"],
    }
