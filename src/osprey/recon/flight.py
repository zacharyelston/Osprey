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

The loop runs in Rust (sim/src/flight.rs, with the tasks' stepping in
sim/src/tasks.rs); this module sets it up and reads it back.

World frame: x east, y north, metres; headings clockwise from north.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey.motion import KN
from osprey.recon import tasks
from osprey.recon.params import payload_w

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
        # A tailsitter has already spent its launch and landing hover from the battery.
        energy = d["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable - d.get("hover_energy_wh", 0.0) * 3600
        return cls(d["mass_total_kg"], d["S_m2"], d["span_m"], d["cd0"], d["k"], p.wing.cl_max,
                   pr.prop_efficiency, pr.motor_efficiency, p.avionics.power_w + payload_w(p),
                   energy, d.get("motor_peak_w", pr.motor_peak_w), d["v_search_ms"], math.radians(p.limits.bank_max_deg))


def _wind(m) -> np.ndarray:
    """Wind as the vector the air moves along (east, north), m/s."""
    a = math.radians(m.wind_from_deg)
    return -m.wind_kn * KN * np.array([math.sin(a), math.cos(a)])


def simulate(p, ac: Aircraft, *, dt: float = 0.5, t_max: float = 3 * 3600.0,
             task_time_max: float | None = None) -> dict:
    """Fly the mission: the task set up here, the loop in Rust (sim/src/flight.rs)."""
    import osprey_sim

    m = p.mission
    wind = _wind(m)
    hb = math.radians(m.boat_heading_deg)
    task = tasks.build(p, wind)
    ac_spec = {"mass_kg": ac.mass_kg, "S_m2": ac.S_m2, "cd0": ac.cd0, "k": ac.k, "cl_max": ac.cl_max,
               "eta_prop": ac.eta_prop, "eta_motor": ac.eta_motor, "p_aux_w": ac.p_aux_w, "energy_j": ac.energy_j,
               "p_shaft_max_w": ac.p_shaft_max_w, "v_search": ac.v_search, "bank_max_rad": ac.bank_max_rad}
    mission = {"wind": wind.tolist(), "boat_v": (m.boat_speed_kn * KN * np.array([math.sin(hb), math.cos(hb)])).tolist(),
               "boat_speed": m.boat_speed_kn * KN, "boat_mode": getattr(m, "boat_mode", "sail"),
               "cruise_alt_m": m.cruise_alt_m, "reserve_frac": m.reserve_frac, "recovery_radius_m": m.recovery_radius_m,
               "t_cap": m.task_time_max_s if task_time_max is None else task_time_max, "dt": dt, "t_max": t_max}
    r = osprey_sim.flight_simulate({k: float(v) for k, v in ac_spec.items()}, mission, task.spec())
    task.absorb(r.pop("task"))
    out = {k: np.array(v) for k, v in r.items() if k not in ("outcome", "why", "phase")}
    out["phase"] = np.array(PHASES)[np.array(r["phase"], dtype=int)]
    out.update(task=task, wind=wind, outcome=PHASES[r["outcome"]], why=r["why"])
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
