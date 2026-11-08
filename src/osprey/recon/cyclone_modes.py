"""The Cyclone's modes, and the manager that moves it between them.

Actuators: A, the motors at the arm tips; A2, optional motors mid-way along each
arm; B, the blade servos that twist each arm about its own axis, and the motors
on it with it.

| Mode | B | A (and A2) | What it is |
|---|---|---|---|
| 1 lift-off and landing | centred: the chords and A point up | lifting | a tricopter: straight up the first 25 ft, clear of the deck, the water and anything near, or down the last |
| 2 spinning hover | pitched off centre, left or right (which way it spins) | pushing round; its PWM, varied once a turn, steers | the whole bird a spinning prop |
| 3 spinning travel | as 2 | as 2, the disc tilted | a rotorcraft, up to the retreating arm's stall |
| 4 wing-borne travel | forward: two arms up, the dihedral wing; one down, the fin | pushing forward; PWM the fine control, B the large | mode 1 turned horizontal |

The moves, each with a guard (what has to be true first) and a cost (time, height, energy):
- 1->2 at the clearance height: B pitched off centre while A holds the height and the spin builds; how fast,
  from the blade elements (cyclone_dynamics), inside a budget of b_ramp_s.
- 2->1 B back to centre, A taking the weight as the spin dies, the same way; then down in mode 1.
- 2->3 the disc tilted, speeding up to mode 3's best-range speed; 3->2 slowing back to a hover.
- 3->4 at height: B driven to centre as the spin dies, A takes the weight pushing up, and the bird pitches
  over to level, A now pushing forward, until wing-borne. A 2-D point mass sets the height and time.
- 4->3 the forced move: pull up hard, the zoom trades speed for height, B twists the arms to the spin
  setting and the inflow spins them up, as an autogyro; powered from there, or not.
- 4->1 tried: pitch up from level until A points up again, A carrying the weight as the wing lets go,
  then down in mode 1. It works only if A's burst holds the weight and the stint fits A's burst time.
A off: in 2 or 3 it comes down like a seed and can flare; in 4 the forced move leads to the same; in 1,
under the clearance height, it falls. That is the exposure, and A2 is what can cover it.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import asdict, dataclass

from osprey.params import _toml, ns
from osprey.recon import cyclone, cyclone_dynamics, flight
from osprey.recon.params import RECON, payload_w

G = 9.81
EDGES = {(1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (4, 1)}
NAMES = {1: "lift-off and landing", 2: "spinning hover", 3: "spinning travel", 4: "wing-borne travel"}


def inputs():
    return ns(_toml(RECON / "cyclone.toml")["modes"])


def stint_s(md) -> float:
    """The longest mode-1 stint of a standard sortie: up to the clearance and B to the spin, or B back
    to centre and down."""
    return max(md.clearance_m / md.climb1_ms + md.b_ramp_s, md.b_ramp_s + md.clearance_m / md.descent1_ms)


def burst_ok(md) -> bool:
    return stint_s(md) <= md.burst_s_max


# --------------------------------------------------------------------------- what each mode takes

def spin_power(p, d: dict, cy, m: dict, vc: float = 0.0) -> float:
    """Mode 2: shaft power spinning in a vertical climb at vc (a descent taken at the hover's power)."""
    h = cyclone.rotor(p, d, cy, m["mass_kg"])
    T = h["thrust_n"]
    vh = math.sqrt(T / (2 * flight.rho(0.0) * cyclone.geometry(p, d, cy)["disc_m2"]))
    vc = max(vc, 0.0)
    induced = cy.induced_factor * T * (vc / 2 + math.sqrt(vc * vc / 4 + vh * vh))
    return (induced + h["p_profile_w"] + h["p_nacelle_w"]) / cy.tip_prop_efficiency


def travel_power(p, d: dict, cy, md, m: dict, v: float) -> float:
    """Mode 3: shaft power spinning along at airspeed v. Induced power from Glauert's inflow, the arms'
    and nacelles' drag growing as 1 + K mu^2, and the hub's drag, through A at the tip speed."""
    h = cyclone.rotor(p, d, cy, m["mass_kg"])
    rho = flight.rho(0.0)
    T = h["thrust_n"]
    vh = math.sqrt(T / (2 * rho * cyclone.geometry(p, d, cy)["disc_m2"]))
    vi = vh
    for _ in range(80):
        vi = 0.5 * vi + 0.5 * vh * vh / math.sqrt(v * v + vi * vi)
    mu = v / h["v_tip_ms"]
    rotor = (cy.induced_factor * T * vi + (h["p_profile_w"] + h["p_nacelle_w"]) * (1 + md.profile_k * mu * mu)
             + 0.5 * rho * v ** 3 * cy.hub_cda_m2)
    return rotor / cy.tip_prop_efficiency


def travel(p, d: dict, cy, md, m: dict) -> dict:
    """Mode 3's speeds: the top (mode 2's wind limit from the blade elements, cyclone_dynamics: the
    retreating arm's stall or B's swing; or A's rating) and the best range."""
    from osprey.recon import cyclone_dynamics

    h = cyclone.rotor(p, d, cy, m["mass_kg"])
    edge = cyclone_dynamics.wind(p, d, cy, m)
    v_stall_arm = edge["two_max_ms"]
    vv = [0.25 * i for i in range(1, int(v_stall_arm / 0.25) + 1)]
    pw = [travel_power(p, d, cy, md, m, v) for v in vv]
    ok = [(v, x) for v, x in zip(vv, pw) if x <= m["motor_peak_w"]]
    top = ok[-1][0] if ok else 0.0
    v_r, p_r = min(ok, key=lambda t: t[1] / t[0])
    return {"v_top_ms": top, "v_range_ms": v_r, "p_range_w": p_r, "p_hover_w": h["p_shaft_w"],
            "limit": edge["two_limit"] if top >= vv[-1] - 1e-9 else "A's rating"}


def _available(p, cy, shaft_w: float, u: float, props: int) -> float:
    """The thrust A (and A2) give along their axis on a shaft power, with the air coming at u."""
    lo, hi = 0.0, 200.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cyclone.lift_power(p, cy, mid, u, props) < shaft_w else (lo, mid)
    return lo


def pitch(p, d: dict, cy, md, m: dict, v0: float, up: bool, dt: float = 0.01) -> dict:
    """3->4 (up=False): from B centred, A pushing up, moving at v0, pitch over to level until wing-borne.
    4->1 (up=True): from level at v0, pitch up until A points up and the bird is down to a hover's drift.
    Either way A (and A2) push at whatever holds the height, up to their burst; where that isn't enough
    the bird sinks, and that is the height lost. A 2-D point mass, a flat plate past the stall, stepped in
    Rust (sim/src/cyclone.rs). The pitch-up has to end hovering on A, so A's burst must hold the weight
    at the end."""
    import osprey_sim

    w = cyclone._wing(p, d, cy)
    S, clm = w["S_m2"], w["cl_max"]
    ar = w["span_m"] ** 2 / S
    W = m["mass_kg"] * G
    v_wing = 1.2 * math.sqrt(2 * W / (flight.rho(0.0) * S * clm))
    r = osprey_sim.cyclone_pitch({
        "prop_diameter_m": cy.tri_prop_diameter_m, "figure_of_merit": cy.tri_figure_of_merit,
        "induced_factor": cy.induced_factor, "S_m2": S, "cl_max": clm, "cla": 2 * math.pi * ar / (ar + 2),
        "cd0": w["cd0"], "k": w["k"], "mass_kg": m["mass_kg"], "v_wing": v_wing,
        "shaft_w": (m["motor_peak_w"] + m["a2_w"]) * cy.burst_factor, "props": m["lift_props"],
        "pitch_rate_rad_s": math.radians(md.pitch_rate_dps), "motor_efficiency": p.propulsion.motor_efficiency,
        "v0": v0, "up": up, "dt": dt})
    return {"t_s": r["t"], "height_lost_m": -r["z_min"], "distance_m": r["x"], "v_ms": r["v"], "v_wing_ms": v_wing,
            "short_s": r["short_s"], "hover_need": r["end_ratio"], "energy_j": r["energy_j"],
            "ok": r["done"] and (not up or r["end_ratio"] <= 1.0 + 1e-6)}


def entry(p, d: dict, cy, md, m: dict, v0: float) -> dict:
    """4->3, the forced move: the zoom trades speed for height, then the inflow spins the arms up while
    it sinks at the seed-fall rate."""
    zoom = md.zoom_efficiency * v0 * v0 / (2 * G)
    loss = cyclone.autorotation(p, d, cy, m)["sink_ms"] * md.entry_s
    return {"v0_ms": v0, "zoom_m": zoom, "entry_loss_m": loss, "net_m": zoom - loss, "t_s": v0 / G + md.entry_s}


# --------------------------------------------------------------------------- the manager

@dataclass
class Phase:
    what: str
    mode: int
    t0_s: float
    dt_s: float
    h0_m: float
    h1_m: float
    v_ms: float
    shaft_w: float
    energy_j: float
    on_a: bool = False              # A carrying the weight: mode 1, the turns of B to and from the spin, 4->1


class Refused(Exception):
    pass


class Manager:
    """Holds the bird's mode, height, speed, time and energy used, and moves it between modes only
    along the edges, only when each move's guard holds, charging each move's cost."""

    def __init__(self, p, d: dict, cy=None, md=None, m: dict | None = None, mode: int = 1, h: float = 0.0,
                 v: float = 0.0):
        self.p, self.d = p, d
        self.cy = cy or cyclone.inputs()
        self.md = md or inputs()
        self.m = m or cyclone.mass(p, d, self.cy)
        self.mode, self.h, self.v, self.t, self.e = mode, h, v, 0.0, 0.0
        self.log: list[Phase] = []
        self.W = self.m["mass_kg"] * G
        self.eta = p.propulsion.motor_efficiency
        self.tr = travel(p, d, self.cy, self.md, self.m)
        self.hover_w = cyclone.rotor(p, d, self.cy, self.m["mass_kg"])["p_shaft_w"]
        self.lift_w = cyclone.lift_power(p, self.cy, self.W, props=self.m["lift_props"])
        self.spin = cyclone_dynamics.spin(p, d, self.cy, self.m)
        self.over = pitch(p, d, self.cy, self.md, self.m, self.tr["v_range_ms"], up=False)
        self.h34 = max(self.md.clearance_m, self.md.safety_height_m + self.over["height_lost_m"])
        w = cyclone._wing(p, d, self.cy)
        self.v4 = 1.2 * math.sqrt(2 * self.W / (flight.rho(0.0) * w["S_m2"] * w["cl_max"]))   # wing-borne, as flown

    def _add(self, what: str, dt: float, h1: float, v: float, shaft: float, energy: float | None = None,
             on_a: bool = False):
        e = shaft * dt / self.eta if energy is None else energy
        self.log.append(Phase(what, self.mode, self.t, dt, self.h, h1, v, shaft, e, on_a or self.mode == 1))
        self.t += dt
        self.e += e
        self.h, self.v = h1, v

    def guard(self, to: int) -> str | None:
        """Why the move can't be made now, or None if it can."""
        md, h = self.md, self.h
        if (self.mode, to) not in EDGES:
            return f"no move from {self.mode} to {to}; go by {' -> '.join(map(str, route(self.mode, to)))}"
        if (self.mode, to) == (1, 2) and h < md.clearance_m - 1e-6:
            return f"spin only at the clearance height, {md.clearance_m:g} m; at {h:.1f} m"
        if (self.mode, to) == (2, 1) and h < md.clearance_m - 1e-6:
            return f"B back to centre only at the clearance height or above; at {h:.1f} m"
        for key, part, verb in (((1, 2), "build", "builds"), ((2, 1), "die", "dies")):
            tr = self.spin[part]
            if (self.mode, to) == key and (not tr["done"] or tr["t_s"] > md.b_ramp_s):
                return (f"the spin {verb} in {tr['t_s']:.1f} s, past B's {md.b_ramp_s:g} s" if tr["done"]
                        else f"the spin never {verb}")
        if (self.mode, to) == (3, 4):
            if h < self.h34 - 1e-6:
                return f"pitch over only from {self.h34:.0f} m; at {h:.1f} m"
            if not self.over["ok"]:
                return "the pitch-over never gets wing-borne"
        if (self.mode, to) == (4, 3) and h < md.safety_height_m - 1e-6:
            return f"the forced move only from {md.safety_height_m:g} m; at {h:.1f} m"
        if (self.mode, to) == (4, 1):
            up = pitch(self.p, self.d, self.cy, md, self.m, self.v, up=True)
            if not up["ok"]:
                return (f"A can't hold the weight at the top: needs {up['hover_need']:.2f} x its burst"
                        if up["hover_need"] > 1 else "the pitch-up never stops")
            if h - up["height_lost_m"] < md.safety_height_m - 1e-6:
                return f"the pitch-up loses {up['height_lost_m']:.0f} m; from {h:.1f} m that is under {md.safety_height_m:g} m"
            stint = up["t_s"] + (h - up["height_lost_m"]) / md.descent1_ms
            if self.m["burst"] and stint > md.burst_s_max:
                return f"the stint on A, {stint:.0f} s, is past its {md.burst_s_max:g} s burst"
        return None

    def go(self, to: int):
        why = self.guard(to)
        if why:
            raise Refused(why)
        md, h = self.md, self.h
        key = (self.mode, to)
        if key == (1, 2):
            b = self.spin["build"]
            self._add("B off centre, the spin builds", b["t_s"], h + b["dz_m"], 0.0, 0.0, energy=b["energy_j"])
        elif key == (2, 1):
            b = self.spin["die"]
            self._add("B to centre, A takes the weight as the spin dies", b["t_s"], h + b["dz_m"], 0.0, 0.0,
                      energy=b["energy_j"], on_a=True)
        elif key == (2, 3):
            a = G * math.tan(math.radians(md.tilt_deg))
            v = self.tr["v_range_ms"]
            self._add("disc tilted, speeding up", v / a, h, v,
                      travel_power(self.p, self.d, self.cy, md, self.m, v / 2))
        elif key == (3, 2):
            a = G * math.tan(math.radians(md.tilt_deg))
            self._add("disc levelled, slowing", self.v / a, h, 0.0,
                      travel_power(self.p, self.d, self.cy, md, self.m, self.v / 2))
        elif key == (3, 4):
            o = pitch(self.p, self.d, self.cy, md, self.m, self.v, up=False)
            b = self.spin["die"]
            self._add("B to centre as the spin dies, pitch over to wing-borne", b["t_s"] + o["t_s"],
                      h - o["height_lost_m"], o["v_ms"], 0.0, energy=b["energy_j"] + o["energy_j"])
        elif key == (4, 3):
            en = entry(self.p, self.d, self.cy, md, self.m, self.v)
            self._add("forced pull-up, the inflow spins it up", en["t_s"], h + en["net_m"], 0.0, 0.0, energy=0.0)
        elif key == (4, 1):
            up = pitch(self.p, self.d, self.cy, md, self.m, self.v, up=True)
            self._add("pitch up until A points up", up["t_s"], h - up["height_lost_m"], 0.0, 0.0, energy=up["energy_j"],
                      on_a=True)
        self.mode = to

    def climb(self, h: float):
        md = self.md
        if self.mode == 1:
            vc = md.climb1_ms
            shaft = cyclone.lift_power(self.p, self.cy, self.W, vc, self.m["lift_props"])
        elif self.mode == 2:
            vc = md.climb2_ms
            shaft = spin_power(self.p, self.d, self.cy, self.m, vc)
        else:
            raise Refused(f"climbs and descents are flown in mode 1 or 2, not {self.mode}")
        self._add(f"mode {self.mode} climb", (h - self.h) / vc, h, 0.0, shaft)

    def descend(self, h: float):
        md = self.md
        if self.mode == 1:
            rate, shaft = md.descent1_ms, self.lift_w
        elif self.mode == 2:
            rate, shaft = md.descent2_ms, self.hover_w
        else:
            raise Refused(f"climbs and descents are flown in mode 1 or 2, not {self.mode}")
        self._add(f"mode {self.mode} descent", (self.h - h) / rate, h, 0.0, shaft)

    def summary(self) -> dict:
        return {"time_s": self.t, "energy_wh": self.e / 3600, "phases": [asdict(x) for x in self.log],
                "mode1_s": sum(x.dt_s for x in self.log if x.on_a)}


def route(frm: int, to: int) -> list[int]:
    """The shortest way along the edges from one mode to another."""
    seen, q = {frm: None}, deque([frm])
    while q:
        n = q.popleft()
        for a, b in EDGES:
            if a == n and b not in seen:
                seen[b] = n
                q.append(b)
    path, n = [], to
    while n is not None:
        path.append(n)
        n = seen.get(n)
    return path[::-1]


# --------------------------------------------------------------------------- sorties

def launch(p, d: dict, cy, md, m: dict) -> Manager:
    """From the deck or the water to wing-borne: 1 up to the clearance, 2, up to the pitch-over height,
    3, 4."""
    mg = Manager(p, d, cy, md, m)
    mg.climb(md.clearance_m)
    mg.go(2)
    mg.climb(mg.h34)
    mg.go(3)
    mg.go(4)
    return mg


def recover(p, d: dict, cy, md, m: dict, direct: bool = False) -> Manager:
    """From wing-borne at the pitch-over height back to the deck: 4, 3, 2, down to the clearance, 1,
    down. Or, tried, 4 straight to 1 from as low as the pitch-up allows, and down."""
    mg = Manager(p, d, cy, md, m, mode=4)
    mg.h, mg.v = mg.h34, mg.v4
    if direct:
        mg.h = direct_height(p, d, cy, md, m, mg.v4)
        mg.go(1)
        mg.descend(0.0)
        return mg
    mg.go(3)
    mg.go(2)
    mg.descend(md.clearance_m)
    mg.go(1)
    mg.descend(0.0)
    return mg


def direct_height(p, d: dict, cy, md, m: dict, v0: float) -> float:
    """The lowest height 4->1 can start from: the pitch-up's loss over the safety height, keeping the
    mode-1 stint after it as short as it can be."""
    return md.safety_height_m + pitch(p, d, cy, md, m, v0, up=True)["height_lost_m"]


_OFF_WING: dict = {}


def off_wing_j(p, d: dict, cy, m: dict) -> float:
    """Electric energy for a standard launch and recovery. The same for every job, so kept."""
    key = (m["mass_kg"], m["motor_peak_w"], m["a2_w"], d["S_m2"], d["span_m"], d["cd0"], d["k"], d["spar_kg"], d["skin_kg"])
    if key not in _OFF_WING:
        md = inputs()
        _OFF_WING[key] = launch(p, d, cy, md, m).e + recover(p, d, cy, md, m).e
    return _OFF_WING[key]


def matrix(p, d: dict, cy, md, m: dict) -> list[dict]:
    """Every move from where it starts in a standard sortie: allowed or not, why, and what it costs."""
    tr = travel(p, d, cy, md, m)
    starts = {1: (md.clearance_m, 0.0), 2: (None, 0.0), 3: (None, tr["v_range_ms"]), 4: (None, None)}
    rows = []
    for a, b in sorted(EDGES):
        mg = Manager(p, d, cy, md, m, mode=a)
        h0, v0 = starts[a]
        mg.h = h0 if h0 is not None else mg.h34
        mg.v = v0 if v0 is not None else mg.v4
        if (a, b) == (4, 1):
            mg.h = direct_height(p, d, cy, md, m, mg.v)
        why = mg.guard(b)
        row = {"from": a, "to": b, "h0_m": mg.h, "v0_ms": mg.v, "ok": why is None, "why": why}
        if why is None:
            mg.go(b)
            ph = mg.log[-1]
            row.update(t_s=ph.dt_s, dh_m=ph.h1_m - ph.h0_m, v1_ms=ph.v_ms, energy_j=ph.energy_j, what=ph.what)
        rows.append(row)
    return rows


def failures(p, d: dict, cy, md, m: dict) -> dict:
    """A motor out, mode by mode. Spinning, it seeds down; wing-borne, the forced move and the same; in
    mode 1, three A motors can't lose one, and the time to fall from the clearance is set against how fast
    B can turn it into a spin. With A2, five of six props are left."""
    au = cyclone.autorotation(p, d, cy, m)
    fall_s = math.sqrt(2 * md.clearance_m / G)
    out = {"seed_ms": au["sink_ms"], "flare_ratio": au["flare_ratio"], "fall_s": fall_s,
           "fall_ms": math.sqrt(2 * G * md.clearance_m), "build_s": cyclone_dynamics.spin(p, d, cy, m)["build"]["t_s"]}
    W = m["mass_kg"] * G
    if m["a2"]:
        left = m["lift_props"] - 1
        shaft = (m["motor_peak_w"] + m["a2_w"]) * cy.burst_factor * left / m["lift_props"]
        out["mode1_one_out"] = _available(p, cy, shaft, 0.0, left) / W
    else:
        out["mode1_one_out"] = 0.0
    return out


def assess(p, d: dict, cy=None, md=None) -> dict:
    """Both lift-off options (A alone, A with A2): the modes' abilities, the move matrix, the standard
    sortie, the tried 4->1 recovery, and a motor out."""
    cy, md = cy or cyclone.inputs(), md or inputs()
    out = {"modes": vars(md), "stint_s": stint_s(md), "burst_ok": burst_ok(md), "dihedral_deg": cy.dihedral_deg}
    for key, a2 in (("A", False), ("A+A2", True)):
        m = cyclone.mass(p, d, cy, a2)
        la, rc = launch(p, d, cy, md, m), recover(p, d, cy, md, m)
        mg = Manager(p, d, cy, md, m, mode=4)
        mg.v = mg.v4
        mg.h = direct_height(p, d, cy, md, m, mg.v)
        why = mg.guard(1)
        direct = recover(p, d, cy, md, m, direct=True).summary() if why is None else {"refused": why}
        tr = travel(p, d, cy, md, m)
        battery = d["battery_kg"] * p.propulsion.battery_wh_per_kg * 3600 * p.propulsion.battery_usable
        aux = p.avionics.power_w + payload_w(p)
        p3 = tr["p_range_w"] / p.propulsion.motor_efficiency + aux
        tr.update(endurance_h=battery / p3 / 3600, range_km=battery / p3 * tr["v_range_ms"] / 1000)
        out[key] = {"mass": m, "travel": tr, "lift_w": la.lift_w, "hover_w": la.hover_w,
                    "pitch_up": pitch(p, d, cy, md, m, la.v4, up=True), "direct_h_m": mg.h,
                    "h34_m": la.h34, "over": la.over, "v4_ms": la.v4, "launch": la.summary(), "recover": rc.summary(),
                    "direct": direct, "matrix": matrix(p, d, cy, md, m), "failures": failures(p, d, cy, md, m)}
    return out


def report(a: dict, title: str) -> str:
    """The modes' sheet: what A, A2 and B do in each, what each can do, every move with its guard and
    cost, the sorties, A alone against A with A2, and a motor out."""
    md = a["modes"]
    sized = "A+A2" if md["a2"] else "A"
    r = a[sized]
    m, tr = r["mass"], r["travel"]
    lines = [f"# The Cyclone's modes: {title}", "",
             "A: the motors at the arm tips. A2: optional motors half-way along each arm. B: the blade servos that "
             "twist each arm about its own axis, and its motors with it. Sized with "
             f"**{'A and A2' if md['a2'] else 'A alone'}**; the other is compared below. REF inputs in `[modes]` of "
             "`design/recon/cyclone.toml`.", "",
             "## The modes", "",
             "| Mode | B | A (A2) | What it can do |", "|---|---|---|---|",
             f"| 1 lift-off and landing | centred: the chords and A point up | lifting | a tricopter: {r['lift_w']:.0f} W to "
             f"hover, {md['climb1_ms']:g} m/s up the first {md['clearance_m']:g} m (25 ft), {md['descent1_ms']:g} m/s down "
             f"the last; peak {m['lift_peak_w']:.0f} W at the burst |",
             f"| 2 spinning hover | pitched off centre, left or right: which way it spins | pushing round; PWM, varied once "
             f"a turn, steers | a spinning prop: {r['hover_w']:.0f} W to hover, {md['climb2_ms']:g} m/s climbs |",
             f"| 3 spinning travel | as 2 | as 2, the disc tilted {md['tilt_deg']:g}° | best range {tr['v_range_ms']:.0f} m/s at "
             f"{tr['p_range_w']:.0f} W; top {tr['v_top_ms']:.0f} m/s ({tr['limit']}); {tr['range_km']:.0f} km on the battery |",
             f"| 4 wing-borne travel | forward: two arms up, the {a['dihedral_deg']:g}° dihedral wing; one down, the fin "
             f"| pushing forward; PWM fine, B large | flies from {r['v4_ms']:.0f} m/s; the jobs, in `cyclone.md` |", "",
             "## The moves", "",
             "Each move from where a standard sortie makes it. A guard is what has to be true first.", "",
             "| Move | From | Guard | Time | Height | Energy | What happens |", "|---|---|---|---|---|---|---|"]
    guards = {(1, 2): f"at {md['clearance_m']:g} m or above", (2, 1): f"at {md['clearance_m']:g} m or above",
              (2, 3): "spinning", (3, 2): "spinning",
              (3, 4): f"from {r['h34_m']:.0f} m: the pitch-over's loss over the {md['safety_height_m']:g} m margin",
              (4, 3): f"from {md['safety_height_m']:g} m", (4, 1): f"A holds the weight at the top, and the stint on A "
              f"under {md['burst_s_max']:g} s"}
    for row in r["matrix"]:
        k = (row["from"], row["to"])
        at = f"{row['h0_m']:.0f} m, {row['v0_ms']:.0f} m/s"
        if row["ok"]:
            lines.append(f"| {k[0]} → {k[1]} | {at} | {guards[k]} | {row['t_s']:.1f} s | {row['dh_m']:+.0f} m | "
                         f"{row['energy_j'] / 3600:.2f} Wh | {row['what']} |")
        else:
            lines.append(f"| {k[0]} → {k[1]} | {at} | {guards[k]} | refused | | | {row['why']} |")
    lines += ["", "Any other move goes along these: 1 to 4 is 1 → 2 → 3 → 4; 4 to 2 is 4 → 3 → 2.", ""]

    def table(name, s):
        out = [f"**{name}:** {s['time_s']:.0f} s, {s['energy_wh']:.2f} Wh, {s['mode1_s']:.0f} s of it on A, carrying "
               "the weight.", "",
               "| Mode | What | Time | Height | Energy |", "|---|---|---|---|---|"]
        for ph in s["phases"]:
            out.append(f"| {ph['mode']} | {ph['what']} | {ph['dt_s']:.1f} s | {ph['h0_m']:.0f} → {ph['h1_m']:.0f} m | "
                       f"{ph['energy_j'] / 3600:.2f} Wh |")
        return out + [""]

    lines += ["## Sorties", ""]
    lines += table("Launch, from the deck or the water to wing-borne", r["launch"])
    lines += table("Recovery, from wing-borne back aboard", r["recover"])
    if "refused" in r["direct"]:
        lines += [f"**Recovery straight from 4 to 1, tried:** refused, {r['direct']['refused']}.", ""]
    else:
        lines += table(f"Recovery straight from 4 to 1, tried (from {r['direct_h_m']:.0f} m, as low as the pitch-up allows)",
                       r["direct"])
        pu = r["pitch_up"]
        lines += [f"The pitch-up from {r['v4_ms']:.0f} m/s takes {pu['t_s']:.1f} s and {pu['distance_m']:.0f} m, loses "
                  f"{pu['height_lost_m']:.1f} m, and ends hovering on A at {pu['hover_need']:.2f} × its burst. It works; it "
                  "just keeps A at its burst, low, for the whole stint.", ""]
    lines += ["## A alone, or A with A2", "",
              "| | A alone | A and A2 |", "|---|---|---|"]
    A, B = a["A"], a["A+A2"]
    rows = [("Mass", lambda x: f"{x['mass']['mass_kg']:.2f} kg"),
            ("Motors", lambda x: f"{x['mass']['motor_kg']:.2f} kg: A {x['mass']['motor_peak_w']:.0f} W"
             + (f", A2 {x['mass']['a2_w']:.0f} W" if x['mass']['a2'] else "")),
            ("Mode 1 hover", lambda x: f"{x['lift_w']:.0f} W"),
            ("Pitch-over (3 → 4): height lost", lambda x: f"{x['over']['height_lost_m']:.0f} m"),
            ("Launch + recovery", lambda x: f"{x['launch']['energy_wh'] + x['recover']['energy_wh']:.1f} Wh"),
            ("One motor out in mode 1", lambda x: f"holds {x['failures']['mode1_one_out']:.2f} × the weight"
             if x['failures']['mode1_one_out'] > 0 else "falls")]
    for name, f in rows:
        lines.append(f"| {name} | {f(A)} | {f(B)} |")
    fa = A["failures"]
    lines += ["", f"Mode 1 is the exposure: {A['launch']['mode1_s'] + A['recover']['mode1_s']:.0f} s a sortie at or under "
              f"{md['clearance_m']:g} m with A alone carrying the weight. Three motors can't lose one, and a fall from {md['clearance_m']:g} m "
              f"takes {fa['fall_s']:.1f} s, less than the {fa['build_s']:.1f} s B needs to turn it into a spin: it hits at "
              f"{fa['fall_ms']:.0f} m/s. With A2, five of six props are left to hold it.", "",
              "## A motor out, mode by mode", "",
              f"- **2 and 3, spinning:** at the burst, one motor holds the spinning hover; with none, it comes down like a "
              f"seed at {fa['seed_ms']:.1f} m/s, and the spin holds {fa['flare_ratio']:.1f}× the sink's energy to flare with.",
              "- **4, wing-borne:** a glider; the forced pull-up (4 → 3) leads to the same seed fall.",
              f"- **1, under {md['clearance_m']:g} m:** see above.", "",
              "The spin building and dying, A's and B's authority, the wind in modes 1 and 2, and floating are in "
              "`dynamics.md` and `water.md`. Not modelled: closed-loop stability in each mode, and the deck's motion."]
    return "\n".join(lines) + "\n"
