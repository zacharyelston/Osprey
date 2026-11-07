"""3-DOF point-mass flight simulation of a Recon mission.

The drone launches from the moving boat and flies to its task (recon/tasks.py):
- a search drifting with a datum;
- a site to survey;
- a vessel to inspect.

It works the task, then returns to the boat. The mission's boat_mode says
what the boat does meanwhile:
- "return" or "approach": it heads for the task and heaves to near it,
  drifting with the water (the man-overboard drill, or arriving at the
  anchorage being scouted);
- "sail": it sails on;
- "hold": it stays where it is, at anchor.

The drone is a point-mass model:
- wind triangle to hold the ground track;
- bank-limited turns with their load factor and induced drag;
- climb limited by excess shaft power;
- an electric energy budget.

It leaves the task for home when the task's goal is met or its pattern ends,
when the task time runs out, or when the battery reaches the energy to get
home plus the reserve ("bingo").

World frame: x east, y north, metres; headings clockwise from north.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey.motion import KN
from osprey.recon import tasks

G = 9.81
PHASES = ("outbound", "task", "return", "recovered", "lost")


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
             task_time_max: float | None = None) -> dict:
    m = p.mission
    wind = _wind(m)
    hb = math.radians(m.boat_heading_deg)
    boat_v = m.boat_speed_kn * KN * np.array([math.sin(hb), math.cos(hb)])
    task = tasks.build(p, wind)
    t_cap = m.task_time_max_s if task_time_max is None else task_time_max
    speeds: dict[tuple[int, int], float] = {}

    def range_speed(alt, headwind):
        key = (int(round(alt / 10)), int(round(headwind * 2)))
        if key not in speeds:
            speeds[key] = ac.best_range_speed(key[0] * 10.0, key[1] / 2)
        return speeds[key]

    boat_mode = getattr(m, "boat_mode", "sail")
    boat_speed = m.boat_speed_kn * KN
    boat = np.zeros(2)
    pos = np.zeros(2)
    e0 = task.entry(0.0, pos)
    h, psi, v = 2.0, math.atan2(e0[0], e0[1]), ac.v_search
    energy = ac.energy_j
    phase, t_task0, why = "outbound", None, "-"
    rec = {k: [] for k in ("t", "x", "y", "h", "v", "phase", "energy", "progress", "power", "bank",
                           "boat_x", "boat_y")}
    t = 0.0
    while t < t_max and phase not in ("recovered", "lost"):
        if phase == "outbound":
            target = task.entry(t, pos)
            far = np.linalg.norm(target - pos) > 600
            h_cmd = m.cruise_alt_m if far else task.alt_m
            if np.linalg.norm(target - pos) < 30:
                phase, t_task0 = "task", t
        if phase == "task":
            target = task.target(t, pos)
            h_cmd = task.alt_m
            # Bingo: the energy to get home along the line to the boat as it is now,
            # against that line's headwind and the boat's speed away along it, plus the reserve.
            to_boat = boat - pos
            home = float(np.linalg.norm(to_boat))
            uh = to_boat / max(home, 1e-6)
            head_home = -float(wind @ uh)
            v_home = range_speed(m.cruise_alt_m, head_home)
            away = float(boat_v @ uh) if boat_mode == "sail" else 0.0
            t_home = home / max(v_home - head_home - away, 1.0)
            bingo = ac.power(v_home, m.cruise_alt_m) * t_home * (1 + m.reserve_frac)
            reason = task.done() or ("time" if t - t_task0 > t_cap else "bingo" if energy <= bingo else None)
            if reason:
                phase, why = "return", reason
        if phase == "return":
            target = boat
            h_cmd = m.cruise_alt_m if np.linalg.norm(boat - pos) > 400 else 15.0
            if np.linalg.norm(boat - pos) < m.recovery_radius_m:
                phase = "recovered"
                continue

        # Speed: task speed on the task, best range for the wind otherwise.
        to = target - pos
        dist = float(np.linalg.norm(to))
        course = math.atan2(to[0], to[1]) if dist > 1e-6 else psi
        u = np.array([math.sin(course), math.cos(course)])
        head = -float(wind @ u)
        v = ac.v_search if phase == "task" else range_speed(h, head)
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
        if phase == "task" and abs(h - task.alt_m) < 15:
            task.look(pos, math.atan2(vg[0], vg[1]), t, dt, float(np.linalg.norm(vg)), h)
        for k_, v_ in (("t", t), ("x", pos[0]), ("y", pos[1]), ("h", h), ("v", v), ("phase", phase),
                       ("energy", energy), ("progress", task.progress), ("power", pw), ("bank", bank),
                       ("boat_x", boat[0]), ("boat_y", boat[1])):
            rec[k_].append(v_)
        pos = pos + vg * dt
        h = max(h + climb * dt, 0.0)
        aim = task.where(t)
        if boat_mode in ("return", "approach") and np.linalg.norm(aim - boat) > 150:
            boat = boat + boat_speed * (aim - boat) / np.linalg.norm(aim - boat) * dt
        elif boat_mode in ("return", "approach"):
            boat = boat + task.drift * dt                  # hove to there, drifting with the water
        elif boat_mode == "sail":
            boat = boat + boat_v * dt
        energy -= pw * dt
        if energy <= 0:
            phase = "lost"
        t += dt

    out = {k: np.array(v_) for k, v_ in rec.items()}
    out.update(task=task, wind=wind, outcome=phase, why=why)
    if task.kind == "search":                              # what the search figures read
        out.update(grid=task.grid, sweep=task.sweep, plan=task.plan, datum0=task.datum0, drift=task.drift,
                   pod=out["progress"], passes=task.passes)
    return out


def summary(p, ac: Aircraft, r: dict) -> dict:
    ph = r["phase"]
    t = r["t"]
    prog = r["progress"]
    task = r["task"]

    def first(mask):
        i = np.flatnonzero(mask)
        return float(t[i[0]]) if i.size else math.inf

    on_scene = first(ph == "task")
    left = first(ph == "return")
    seg = np.hypot(np.diff(r["x"]), np.diff(r["y"]))
    done = float(prog[-1]) if prog.size else 0.0
    s = {
        "kind": task.kind,
        "progress_label": task.progress_label,
        "outcome": r["outcome"],
        "left_task_because": r["why"],
        "goal": task.goal,
        "progress": done,
        "goal_met": bool(done >= task.goal - 1e-6 or r["why"] == "pattern" and done >= 0.9 * task.goal),
        "flight_time_s": float(t[-1]) if t.size else 0.0,
        "on_scene_s": on_scene,
        "task_s": (left - on_scene) if math.isfinite(left) else math.inf,
        "t_half_s": first(prog >= 0.5 * task.goal),
        "t_goal_s": first(prog >= task.goal - 1e-6),
        "distance_km": float(seg.sum() / 1e3),
        "energy_left_frac": float(r["energy"][-1] / ac.energy_j) if t.size else 0.0,
        "bank_max_deg": float(np.degrees(np.abs(r["bank"]).max())) if t.size else 0.0,
        "power_mean_w": float(np.mean(r["power"])) if t.size else 0.0,
        **task.info(),
    }
    if task.kind == "search":
        s.update(pod=done, pod_planned=task.plan.pod, t_pod50_s=first(prog >= 0.5), t_pod90_s=first(prog >= 0.9),
                 left_search_because=r["why"], search_s=s["task_s"], search_passes=task.passes)
    return s
