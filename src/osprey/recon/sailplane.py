"""The sailplane: a 4.8 m thermal-soaring relay, taken from an engineering handoff package to parts.

A laminar body of revolution (a Myring body) carries a three-piece wing. The centre section is built round
a space-frame of pultruded carbon tubes: four spanwise chords in two Warren planes, braced top, bottom and
across, standing on four pylons that land in the body's two main bulkheads. Outer panels plug on with a
square joiner. Everything is read from design/recon/sailplane.toml.

This module:
- lays the frame out as nodes and members (`truss`), exactly as the package's OpenSCAD drew it;
- flies it through a pull-up (`loads`, `solve`): an elliptic lift, less the wing's own weight, put into a
  3-D frame of beam elements (the lugs are bonded, so the joints carry moment), for the tubes' axial loads,
  bending, Euler buckling and stress (`evaluate`);
- sets every lug's sockets (`lugs`): each tube stops where its bore clears its neighbours', which fixes the
  cut length of every tube (`cut_list`);
- checks the package against itself (`checks`): does the frame fit in the wing section, does the tail cone
  close where it says, does the pack hold what it says;
- writes the parts as parametric OpenSCAD (`export`): the node lugs, the joiner receptacle, the centre wing
  with its ribs, flaps and root fairing, and the belly's flat for the camera. src/osprey/recon/scad holds
  the modules; `export` writes params.scad beside them from the design file and the lugs' solved sockets.

Stations in millimetres: x aft from the nose tip, y to starboard, z up from the body's axis.
"""

from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path

import numpy as np

from osprey.params import _toml, ns
from osprey.recon.params import RECON

G = 9.81
SCAD = Path(__file__).parent / "scad"
CASES = ("day", "night")


def inputs():
    return ns(_toml(RECON / "sailplane.toml"))


# ---- the body and the wing section ------------------------------------------------------------------------

def myring_r(f, x, clamp: bool = True):
    """The body's radius at station x (mm). The tail cone's cubic closes at the full length; with `clamp`
    it is not let below the spinner's radius, as the package's OpenSCAD has it."""
    a, b, R = f.nose_mm, f.mid_mm, f.radius_mm
    c = f.length_mm - a - b
    x = np.asarray(x, float)
    nose = R * np.clip(1.0 - ((np.clip(x, 0.0, a) - a) / a) ** 2, 0.0, None) ** (1.0 / f.nose_exp)
    dx = np.clip(x - a - b, 0.0, None)
    t = math.tan(math.radians(f.tail_angle_deg))
    tail = R - (3 * R / c**2 - t / c) * dx**2 + (2 * R / c**3 - t / c**2) * dx**3
    if clamp:
        tail = np.maximum(tail, f.spinner_r_mm)
    return np.where(x < a, nose, np.where(x <= a + b, R, tail))


def airfoil(name: str):
    """A section's points as given (from the trailing edge over the top and back), and its upper and lower
    surfaces from the nose aft, in chord units."""
    pts = np.loadtxt(RECON / "airfoils" / f"{name}.dat", skiprows=1)
    i = int(np.argmin(pts[:, 0]))
    return pts, pts[: i + 1][::-1], pts[i:]


def surface_z(s, x_mm):
    """The centre section's upper and lower surface heights (mm) at station x."""
    w = s.wing
    _, up, lo = airfoil(w.airfoil)
    xc = (np.asarray(x_mm, float) - w.le_x_mm) / w.chord_mm
    return (w.chord_z_mm + w.chord_mm * np.interp(xc, up[:, 0], up[:, 1]),
            w.chord_z_mm + w.chord_mm * np.interp(xc, lo[:, 0], lo[:, 1]))


# ---- the frame --------------------------------------------------------------------------------------------

def _nid(plane: str, level: str, y: float) -> str:
    return f"{plane}{level}{y:+.0f}"


def joiner_plates(s) -> tuple[float, float]:
    """The mid-planes (|y|, mm) of the joiner box's outer and inner plates. The outer one sits just inboard
    of the tip lugs' chord sleeves; the inner one is at the joiner's inboard end."""
    half = s.wing.center_span_mm / 2
    return half - s.lug.socket_mm - 1.0 - s.joiner.plate_mm / 2, half - s.joiner.engage_mm + s.joiner.plate_mm / 2


def truss(s) -> tuple[dict, list[dict]]:
    """Nodes (name -> xyz, mm) and members. A chord is one tube, split here wherever something lands on it."""
    t, j = s.truss, s.joiner
    half, n = s.wing.center_span_mm / 2, t.bays_per_side
    bay = half / n
    ys = [i * bay for i in range(-n, n + 1)]
    X = {"F": t.x_front_mm, "R": t.x_rear_mm}
    Z = {"B": t.z_bot_mm, "T": t.z_top_mm}
    nodes: dict[str, np.ndarray] = {}
    members: list[dict] = []

    def node(p, lv, y):
        k = _nid(p, lv, y)
        nodes.setdefault(k, np.array([X[p], y, Z[lv]], float))
        return k

    def add(group, a, b, tube="strut", **kw):
        members.append({"name": f"{a}>{b}", "group": group, "a": a, "b": b, "tube": tube, **kw})

    yo, yi = joiner_plates(s)
    on_chord = {lv: sorted(set(ys) | {sg * y for sg in (-1, 1) for y in (yo, yi)}
                           | ({-t.pylon_y_mm, t.pylon_y_mm} if lv == "B" else set()))
                for lv in "BT"}
    for p in "FR":
        for lv in "BT":
            yy = on_chord[lv]
            for y1, y2 in zip(yy[:-1], yy[1:]):
                add("chord", node(p, lv, y1), node(p, lv, y2), "chord", chord=f"{p}{lv}")
    for y in ys:
        for p in "FR":
            add("post", node(p, "B", y), node(p, "T", y))
        for lv in "BT":
            add("cross brace", node("F", lv, y), node("R", lv, y))
        if not (j.replaces_tip_diagonal and abs(abs(y) - half) < 1e-6):
            add("station diagonal", node("F", "B", y), node("R", "T", y))
    for i in range(-n, n):
        y1, y2, flip = i * bay, (i + 1) * bay, abs(i) % 2 == 0
        for p in "FR":
            add("face diagonal", node(p, "B" if flip else "T", y1), node(p, "T" if flip else "B", y2))
        for lv in "BT":
            add("planform diagonal", node("F" if flip else "R", lv, y1), node("R" if flip else "F", lv, y2))
    for p in "FR":
        for sg in (-1, 1):
            y = sg * t.pylon_y_mm
            foot = f"{p}P{y:+.0f}"
            nodes[foot] = np.array([X[p], y, t.pylon_foot_z_mm], float)
            add("pylon", node(p, "B", y), foot, "chord")
    return nodes, members


def section(tube) -> tuple[float, float]:
    """A round tube's area (mm^2) and second moment (mm^4)."""
    return (math.pi / 4 * (tube.od_mm**2 - tube.id_mm**2), math.pi / 64 * (tube.od_mm**4 - tube.id_mm**4))


def _k_local(E, Gs, A, I, L) -> np.ndarray:
    k = np.zeros((12, 12))
    a, t = E * A / L, Gs * 2 * I / L
    b1, b2, b3, b4 = 12 * E * I / L**3, 6 * E * I / L**2, 4 * E * I / L, 2 * E * I / L
    terms = [(0, 0, a), (0, 6, -a), (6, 6, a), (3, 3, t), (3, 9, -t), (9, 9, t),
             (1, 1, b1), (1, 5, b2), (1, 7, -b1), (1, 11, b2), (5, 5, b3), (5, 7, -b2), (5, 11, b4),
             (7, 7, b1), (7, 11, -b2), (11, 11, b3),
             (2, 2, b1), (2, 4, -b2), (2, 8, -b1), (2, 10, -b2), (4, 4, b3), (4, 8, b2), (4, 10, b4),
             (8, 8, b1), (8, 10, b2), (10, 10, b3)]
    for i, j, v in terms:
        k[i, j] = k[j, i] = v
    return k


def _rotation(d: np.ndarray) -> np.ndarray:
    ex = d / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    ey = np.cross(ref, ex)
    ey /= np.linalg.norm(ey)
    return np.array([ex, ey, np.cross(ex, ey)])


def solve(s, nodes: dict, members: list[dict], F: dict) -> dict:
    """The frame under nodal forces F (name -> [fx, fy, fz], N), held at the pylons' feet (pinned to the
    bulkheads). Returns each member's axial load (N, tension positive) and largest end moment (N mm), and
    the feet's reactions."""
    idx = {k: i for i, k in enumerate(nodes)}
    E, Gs = s.carbon.e_gpa * 1e3, s.carbon.g_gpa * 1e3
    K = np.zeros((6 * len(nodes),) * 2)
    els = []
    for m in members:
        a, b = nodes[m["a"]], nodes[m["b"]]
        A, I = section(getattr(s.tube, m["tube"]))
        L = float(np.linalg.norm(b - a))
        k = _k_local(E, Gs, A, I, L)
        T = np.kron(np.eye(4), _rotation(b - a))
        dof = np.r_[6 * idx[m["a"]] + np.arange(6), 6 * idx[m["b"]] + np.arange(6)]
        K[np.ix_(dof, dof)] += T.T @ k @ T
        els.append((k, T, dof, L))
    f = np.zeros(6 * len(nodes))
    for k_, v in F.items():
        f[6 * idx[k_]: 6 * idx[k_] + 3] += v
    feet = [k_ for k_ in nodes if k_[1] == "P"]
    fixed = np.array([6 * idx[k_] + d for k_ in feet for d in range(3)])
    free = np.setdiff1d(np.arange(len(f)), fixed)
    u = np.zeros_like(f)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
    react = (K @ u - f)[fixed].reshape(-1, 3)
    out = []
    for m, (k, T, dof, L) in zip(members, els):
        q = k @ T @ u[dof]
        out.append({"name": m["name"], "length_mm": L, "axial_n": float(q[6]),
                    "moment_nmm": float(max(math.hypot(q[4], q[5]), math.hypot(q[10], q[11])))})
    return {"members": out, "reactions_n": {k_: r.tolist() for k_, r in zip(feet, react)},
            "applied_z_n": float(f[2::6].sum()), "tip_deflection_mm": float(max(
                u[6 * idx[k_] + 2] for k_ in nodes if abs(abs(nodes[k_][1]) - s.wing.center_span_mm / 2) < 1e-6))}


# ---- the pull-up ------------------------------------------------------------------------------------------

def _lift(s, total_n: float, y0: float, y1: float) -> tuple[float, float]:
    """An elliptic lift's force (N) between span stations y0 and y1 (mm), and its moment about y0 (N mm)."""
    h = s.wing.span_mm / 2
    y = np.linspace(y0, y1, 401)
    l = 2 * total_n / (math.pi * h) * np.sqrt(np.clip(1 - (y / h) ** 2, 0, None))
    return float(np.trapezoid(l, y)), float(np.trapezoid(l * (y - y0), y))


def loads(s, case: str = "day") -> tuple[dict, dict]:
    """Nodal forces on the frame in the pull-up, and what they add up to. All the lift is taken on the wing
    (none on the body, no tail load), elliptic over the whole span; each part of the wing's own weight comes
    off where it is. The pull-up is flown at the speed where the wing just reaches it, stall x sqrt(n)."""
    w, t, j, n = s.wing, s.truss, s.joiner, s.loads.n
    auw = s.mass.auw_kg if case == "day" else s.mass.auw_night_kg
    m_panel = w.panel_day_kg if case == "day" else w.panel_night_kg
    L = n * G * auw
    half, d = w.center_span_mm / 2, t.x_rear_mm - t.x_front_mm
    x_qc, x_mid = w.le_x_mm + 0.25 * w.chord_mm, (t.x_front_mm + t.x_rear_mm) / 2
    q = 0.5 * s.flight.rho_kgm3 * (s.flight.stall_clean_ms * math.sqrt(n)) ** 2 * 1e-6      # N/mm^2
    F: dict[str, np.ndarray] = {}

    def vertical(y, fz, x_at, nose_down_nmm=0.0):
        ff = (t.x_rear_mm - x_at) / d
        for p, v in (("F", fz * ff - nose_down_nmm / d), ("R", fz * (1 - ff) + nose_down_nmm / d)):
            for lv in "BT":
                k = _nid(p, lv, y)
                F[k] = F.get(k, np.zeros(3)) + np.array([0.0, 0.0, v / 2])

    nb = t.bays_per_side
    bay = half / nb
    lift_c = 0.0
    for i in range(-nb, nb + 1):
        lo, hi = max(-half, (i - 0.5) * bay), min(half, (i + 0.5) * bay)
        li, _ = _lift(s, L, lo, hi)
        lift_c += li
        vertical(i * bay, li, x_qc, -q * w.chord_mm**2 * w.cm * (hi - lo))
        vertical(i * bay, -n * G * w.center_kg * (hi - lo) / w.center_span_mm, x_mid)
    lp, mp = _lift(s, L, half, w.span_mm / 2)
    panel_l = w.span_mm / 2 - half
    cr, ct = w.chord_mm, w.tip_chord_mm
    arm = panel_l / 3 * (cr + 2 * ct) / (cr + ct)
    shear = lp - n * G * m_panel
    bend = mp - n * G * m_panel * arm
    nose_down = -q * w.cm * panel_l * (cr**2 + cr * ct + ct**2) / 3 - lp * (j.x_mm - x_qc)
    yo, yi = joiner_plates(s)
    for sg in (-1, 1):
        vertical(sg * yo, shear + bend / (yo - yi), j.x_mm, nose_down)
        vertical(sg * yi, -bend / (yo - yi), j.x_mm)
    return F, {"case": case, "auw_kg": auw, "lift_n": L, "center_lift_n": lift_c, "panel_lift_n": lp,
               "joiner_shear_n": shear, "joiner_moment_nm": bend / 1e3, "joiner_couple_n": bend / (yo - yi),
               "speed_ms": s.flight.stall_clean_ms * math.sqrt(n)}


def evaluate(s, members: list[dict], res: dict) -> list[dict]:
    """Each member's margins at ultimate (limit x fs): Euler buckling between its ends, pinned (the lugs'
    fixity is not counted), and stress, axial plus bending, against the tube's allowables."""
    E, fs, rows = s.carbon.e_gpa * 1e3, s.loads.fs, []
    for m, r in zip(members, res["members"]):
        tube = getattr(s.tube, m["tube"])
        A, I = section(tube)
        N, M, L = r["axial_n"], r["moment_nmm"], r["length_mm"]
        pcr = math.pi**2 * E * I / L**2
        sigma = abs(N) / A + M / (2 * I / tube.od_mm)
        allow = s.carbon.comp_allow_mpa if N < 0 else s.carbon.tens_allow_mpa
        rows.append({**m, **r, "pcr_n": pcr, "sigma_mpa": sigma,
                     "u_buckle": fs * max(-N, 0.0) / pcr, "u_stress": fs * sigma / allow})
    return rows


def pull_up(s, nodes, members) -> dict:
    out = {}
    for case in CASES:
        F, summary = loads(s, case)
        res = solve(s, nodes, members, F)
        rows = evaluate(s, members, res)
        out[case] = {**summary, "reactions_n": res["reactions_n"], "applied_z_n": res["applied_z_n"],
                     "tip_deflection_mm": res["tip_deflection_mm"], "members": rows,
                     "u_max": max(max(r["u_buckle"], r["u_stress"]) for r in rows)}
    out["governing"] = max(CASES, key=lambda c: out[c]["u_max"])
    return out


# ---- the lugs and the cut list ----------------------------------------------------------------------------

def _bore_points(d: np.ndarray, r: float, t0: float, t1: float) -> np.ndarray:
    R = _rotation(d)
    t = np.linspace(t0, t1, 16)[:, None, None]
    a = np.linspace(0, 2 * math.pi, 16, endpoint=False)[None, :, None]
    ring = r * (np.cos(a) * R[1] + np.sin(a) * R[2])
    return np.r_[(t * R[0] + ring).reshape(-1, 3), (t * R[0]).reshape(-1, 3)]


def _to_segment(P: np.ndarray, d: np.ndarray, t0: float, t1: float) -> np.ndarray:
    return np.linalg.norm(P - np.clip(P @ d, t0, t1)[:, None] * d, axis=1)


def lugs(s, nodes: dict, members: list[dict]) -> dict:
    """Every printed lug: the tubes that meet at a node, each as an arm {member, dir, od, kind, seat}.
    kind 1 is a chord passing through, 2 a chord ending in a capped socket (the tips), 0 a socket: its tube
    stops `seat` mm short of the node's centre, the least that leaves `web` between its bore and every
    other's. A shallow diagonal is pushed a long way out along its chord before it clears it."""
    lg, far = s.lug, 400.0
    gap, depth = lg.bond_gap_mm, lg.socket_mm
    overrun = s.tube.strut.od_mm / 2 + gap + lg.wall_mm        # a tip chord runs on to the far side of the lug
    out = {}
    for k, p in nodes.items():
        if k[1] == "P":
            continue
        arms, chord_dirs = [], []
        for m in members:
            if k not in (m["a"], m["b"]):
                continue
            d = nodes[m["b"] if m["a"] == k else m["a"]] - p
            d = d / np.linalg.norm(d)
            if m["group"] == "chord":
                chord_dirs.append(d)
            else:
                arms.append({"member": m["name"], "dir": d, "od": getattr(s.tube, m["tube"]).od_mm,
                             "kind": 0, "seat": 0.0})
        if len(arms) == 0:
            continue                                            # where a joiner plate threads on: no lug
        through = len(chord_dirs) == 2
        arms.insert(0, {"member": "chord", "dir": np.array([0.0, 1.0, 0.0]) if through else chord_dirs[0],
                        "od": s.tube.chord.od_mm, "kind": 1 if through else 2, "seat": 0.0 if through else overrun})

        def span(a):
            return {0: (a["seat"], a["seat"] + depth), 1: (-far, far), 2: (-a["seat"], far)}[a["kind"]]

        for _ in range(4000):
            moved = False
            for a in arms[1:]:
                P = _bore_points(a["dir"], a["od"] / 2 + gap, *span(a))
                if any(_to_segment(P, b["dir"], *span(b)).min() < b["od"] / 2 + gap + lg.web_mm - 1e-9
                       for b in arms if b is not a):
                    a["seat"] += 0.5
                    moved = True
            if not moved:
                break
        out[k] = arms
    return out


def cut_list(s, nodes: dict, members: list[dict], lg: dict) -> list[dict]:
    """Every tube to cut: a strut's length is its nodes' distance less the two seats; a chord is one piece
    through every lug, running on into the tip lugs' caps. A pylon's foot fitting is not designed here: it
    is cut to its foot node."""
    seat = {(k, a["member"]): a["seat"] for k, arms in lg.items() for a in arms}
    rows = []
    for c in sorted({m["chord"] for m in members if m["group"] == "chord"}):
        cap = next(a["seat"] for arms in lg.values() for a in arms if a["kind"] == 2)
        rows.append({"part": f"chord {c}", "group": "chord", "tube": "chord",
                     "cut_mm": s.wing.center_span_mm + 2 * cap, "in_sockets_mm": 0.0})
    for m in members:
        if m["group"] == "chord":
            continue
        L = float(np.linalg.norm(nodes[m["b"]] - nodes[m["a"]]))
        sa, sb = seat.get((m["a"], m["name"]), 0.0), seat.get((m["b"], m["name"]), 0.0)
        ends = sum((k, m["name"]) in seat for k in (m["a"], m["b"]))
        rows.append({"part": m["name"], "group": m["group"], "tube": m["tube"], "cut_mm": L - sa - sb,
                     "in_sockets_mm": ends * s.lug.socket_mm, "seats_mm": [sa, sb]})
    return rows


def bom(s, cuts: list[dict]) -> list[dict]:
    """The cut list gathered into like pieces, with the bulkhead plates and the rails."""
    rho = s.carbon.rho_kgm3 * 1e-9
    groups: dict[tuple, int] = {}
    for c in cuts:
        key = (c["group"], c["tube"], round(c["cut_mm"], 1))
        groups[key] = groups.get(key, 0) + 1
    rows = []
    for (g, tube, cut), qty in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], -kv[0][2])):
        tb = getattr(s.tube, tube)
        rows.append({"item": g, "stock": f"carbon tube {tb.od_mm:g} x {tb.id_mm:g} mm", "qty": qty, "cut_mm": cut,
                     "note": "", "mass_g": qty * cut * section(tb)[0] * rho * 1e3})
    for b in s.bulkhead:
        r = float(myring_r(s.fuselage, b.x_mm)) - s.fuselage.wall_mm
        rows.append({"item": f"ring bulkhead, x = {b.x_mm:g}", "stock": f"{b.material} plate, {b.t_mm:g} mm", "qty": 1,
                     "cut_mm": 2 * r, "note": f"ring {2 * r:.1f} OD x {2 * max(10.0, r - b.web_mm):.1f} ID; "
                                             f"blank {2 * r:.0f} x {2 * r:.0f}", "mass_g": None})
    ra = s.rails
    rows.append({"item": "CG trim rail", "stock": f"{ra.material}, {ra.section_mm:g} mm", "qty": 2,
                 "cut_mm": ra.x_mm[1] - ra.x_mm[0], "note": f"y = +/-{ra.y_mm:g}, z = {ra.z_mm:g}", "mass_g": None})
    return rows


# ---- the belly's flat, the joiner and the flaps -----------------------------------------------------------

def nadir_flat(s) -> dict:
    """A flat for the camera's window: the body cut by one plane, through the hull where the pane's two ends
    are, wide enough there for the pane. A convex body cut by a plane leaves a flat facet and no step, so
    the flat follows the nose's slope instead of being recessed across it."""
    nd, f = s.nadir, s.fuselage
    pane = nd.window_mm + 2 * nd.ledge_mm
    xc = (nd.x_mm[0] + nd.x_mm[1]) / 2
    xa, xb = xc - pane / 2 - nd.margin_mm, xc + pane / 2 + nd.margin_mm
    hw = pane / 2 + nd.margin_mm
    za, zb = (-math.sqrt(float(myring_r(f, x)) ** 2 - hw**2) for x in (xa, xb))
    slope = (zb - za) / (xb - xa)
    x = np.arange(0.0, f.truncate_mm, 1.0)
    r = myring_r(f, x)
    cut = r > -(za + slope * (x - xa))                 # where the plane is inside the hull
    half_w = np.sqrt(np.clip(r**2 - (za + slope * (x - xa)) ** 2, 0, None))
    return {"pane_mm": pane, "xa_mm": xa, "za_mm": za, "tilt_deg": math.degrees(math.atan(-slope)),
            "from_mm": float(x[cut][0]), "to_mm": float(x[cut][-1]), "max_half_w_mm": float(half_w[cut].max()),
            "depth_mm": float((r + za + slope * (x - xa))[cut].max()), "window_x_mm": [xc - nd.window_mm / 2,
                                                                                    xc + nd.window_mm / 2]}


def joiner_fit(s) -> dict:
    """The joiner sleeve, tilted to the dihedral about the middle of its engagement at the frame's
    mid-depth: its room between the planform diagonals, and inside the wing's skin."""
    j, t, w = s.joiner, s.truss, s.wing
    half_h = (j.size_mm / 2 + j.gap_mm + j.wall_mm) / math.cos(math.radians(w.dihedral_deg))
    rise = j.engage_mm / 2 * math.tan(math.radians(w.dihedral_deg))
    zc = (t.z_bot_mm + t.z_top_mm) / 2
    up, lo = surface_z(s, [j.x_mm - half_h, j.x_mm + half_h])
    return {"half_h_mm": half_h, "rise_mm": rise, "z_mm": zc,
            "to_diagonals_mm": (t.z_top_mm - t.z_bot_mm) / 2 - s.tube.strut.od_mm / 2 - half_h - rise,
            "to_skin_mm": min(float(up.min()) - w.skin_mm - (zc + half_h + rise),
                              (zc - half_h - rise) - (float(lo.max()) + w.skin_mm))}


def flap_split(s) -> dict:
    """Where the centre flaps must start: fully down as a brake, a flap's trailing edge comes below the
    body's crown line, so nothing can swing over the body or the fairing."""
    w, fl = s.wing, s.flap
    cf = fl.chord_frac * w.chord_mm
    xh = w.le_x_mm + w.chord_mm - cf
    zh = float(surface_z(s, xh)[1])
    a = math.radians(fl.crow_deg)
    x_te, z_te = xh + cf * math.cos(a), zh - cf * math.sin(a)
    r = float(myring_r(s.fuselage, x_te))
    clash = math.sqrt(max(r**2 - z_te**2, 0.0)) if abs(z_te) < r else 0.0
    return {"hinge_x_mm": xh, "hinge_z_mm": zh, "te_down_z_mm": z_te, "clash_half_w_mm": clash,
            "inboard_y_mm": max(clash, s.fairing.half_w_mm) + s.fairing.fillet_mm}


# ---- the package against itself ---------------------------------------------------------------------------

def checks(s, pu: dict, cuts: list[dict]) -> list[dict]:
    """Design findings: ok is True, False (a FAIL) or None (a note)."""
    out = []

    def add(name, ok, text):
        out.append({"name": name, "ok": ok, "text": text})

    t, w, f, b = s.truss, s.wing, s.fuselage, s.battery
    od = s.tube.chord.od_mm
    need = t.z_top_mm - t.z_bot_mm + od
    room = {}
    for nm, x in (("front", t.x_front_mm), ("rear", t.x_rear_mm)):
        up, lo = surface_z(s, x)
        room[nm] = float(up - lo) - 2 * w.skin_mm
    add("frame inside the wing section", all(v >= need for v in room.values()),
        f"the frame is {need:.0f} mm deep over its chords; inside the {w.airfoil.upper()}'s skin there is "
        f"{room['front']:.1f} mm at the front plane and {room['rear']:.1f} mm at the rear. The deepest frame that "
        f"fits has its chords' centres {max(room['front'] - od, 0):.1f} mm apart at the front and "
        f"{max(room['rear'] - od, 0):.1f} mm at the rear")
    g = pu[pu["governing"]]
    for grp, label in (("chord", "chords"), (None, "posts, braces and diagonals"), ("pylon", "pylons")):
        rows = [r for r in g["members"] if (r["group"] == grp if grp else r["group"] not in ("chord", "pylon"))]
        wb, ws = max(rows, key=lambda r: r["u_buckle"]), max(rows, key=lambda r: r["u_stress"])
        add(f"{label} at {s.loads.n:g} g x {s.loads.fs:g}", wb["u_buckle"] <= 1 and ws["u_stress"] <= 1,
            (f"buckling {wb['u_buckle']:.2f} of critical ({wb['name']}: {-wb['axial_n']:.0f} N on {wb['length_mm']:.0f} mm, "
             f"critical {wb['pcr_n']:.0f} N)" if wb["u_buckle"] > 0 else "all in tension") + f"; stress {ws['u_stress']:.2f} of allowable ({ws['name']}: {ws['sigma_mpa']:.0f} MPa)")
    short = [c for c in cuts if c["group"] != "chord" and c["cut_mm"] - c["in_sockets_mm"] < s.lug.min_bare_mm]
    add("every tube longer than its sockets", not short,
        "all are" if not short else f"{len(short)} are not: " + ", ".join(sorted({
            f"{c['group']} ({c['cut_mm']:.1f} mm cut, {c['in_sockets_mm']:.0f} mm of socket)" for c in short})))
    add("chords clear the body's crown", t.z_bot_mm - od / 2 > f.radius_mm,
        f"{t.z_bot_mm - od / 2 - f.radius_mm:.1f} mm under the bottom chords")
    r_in = f.radius_mm - f.wall_mm
    r_foot = math.hypot(t.pylon_y_mm, t.pylon_foot_z_mm)
    web = next(bh.web_mm for bh in s.bulkhead if bh.x_mm == t.x_front_mm)
    add("pylon feet land in the main bulkheads' webs", r_in - web <= r_foot <= r_in,
        f"feet at radius {r_foot:.1f} mm; the web runs {r_in - web:.1f} to {r_in:.1f} mm")
    jf = joiner_fit(s)
    add("joiner sleeve between the planform diagonals", jf["to_diagonals_mm"] >= 0, f"{jf['to_diagonals_mm']:.1f} mm to spare")
    add("joiner sleeve inside the wing's skin", jf["to_skin_mm"] >= 0,
        f"{jf['to_skin_mm']:.1f} mm: a {s.joiner.size_mm:g} mm joiner tilted {w.dihedral_deg:g} deg over "
        f"{s.joiner.engage_mm:g} mm needs {2 * (jf['half_h_mm'] + jf['rise_mm']):.1f} mm of depth")
    r_end = float(myring_r(f, f.truncate_mm, clamp=False))
    x = np.arange(f.nose_mm + f.mid_mm, f.truncate_mm, 0.5)
    rr = myring_r(f, x, clamp=False)
    x22 = float(x[np.argmax(rr < f.spinner_r_mm)])
    steep = math.degrees(math.atan(float(np.max(-np.gradient(rr, x)))))
    add("tail cone meets the spinner at the firewall", abs(r_end - f.spinner_r_mm) < 1.0,
        f"the cubic is down to {r_end:.1f} mm radius at x = {f.truncate_mm:g}, not {f.spinner_r_mm:g}: it reaches the "
        f"spinner's radius at x = {x22:.0f}, and held there the last {f.truncate_mm - x22:.0f} mm are a parallel "
        f"stinger. Cut at x = {x22:.0f} or close the cubic on the spinner. Its steepest slope is {steep:.1f} deg")
    nf = nadir_flat(s)
    add("belly flat ends ahead of the tail cone's recovery", nf["to_mm"] < s.nadir.recovery_from_mm,
        f"one plane tilted {nf['tilt_deg']:.1f} deg nose-up, flat from x = {nf['from_mm']:.0f} to {nf['to_mm']:.0f}, "
        f"up to {2 * nf['max_half_w_mm']:.0f} mm wide and {nf['depth_mm']:.1f} mm off the round")
    wh = b.cells * b.cell_v * b.cell_ah
    add("battery holds what it weighs", abs(wh - b.quoted_wh) / b.quoted_wh < 0.15,
        f"{b.cells} cells are {b.cells * b.cell_kg:.2f} kg and {wh:.0f} Wh ({b.cells // b.series}P, "
        f"{b.cells // b.series * b.cell_ah:.0f} Ah), not {b.quoted_wh:.0f} Wh; {b.quoted_ah:g} Ah at {b.series}S is "
        f"{round(b.quoted_ah / b.cell_ah) * b.series} cells, {round(b.quoted_ah / b.cell_ah) * b.series * b.cell_kg:.1f} kg. "
        f"The loiter needs {b.loiter_w * b.loiter_h:.0f} Wh")
    area = (w.center_span_mm * w.chord_mm + (w.span_mm - w.center_span_mm) * (w.chord_mm + w.tip_chord_mm) / 2) / 1e6
    add("wing area", None, f"{area:.3f} m^2 from the planform (quoted {w.quoted_area_m2:g}), aspect ratio "
                           f"{(w.span_mm / 1e3) ** 2 / area:.1f} (quoted {w.quoted_ar:g}), "
                           f"{s.mass.auw_kg / area * 10:.0f} g/dm^2 by day")
    cl = 2 * s.mass.auw_kg * G / (s.flight.rho_kgm3 * s.flight.stall_clean_ms**2 * area)
    add("stall speed", None, f"{s.flight.stall_clean_ms:g} m/s clean at {s.mass.auw_kg:g} kg takes a lift "
                             f"coefficient of {cl:.2f}")
    fs_ = flap_split(s)
    add("centre flaps", None, f"hinge at x = {fs_['hinge_x_mm']:.0f}; {s.flap.crow_deg:g} deg down the trailing edge is at "
                              f"z = {fs_['te_down_z_mm']:.0f}, inside the body within {fs_['clash_half_w_mm']:.0f} mm of the "
                              f"centreline, so the flaps start at y = +/-{fs_['inboard_y_mm']:.0f} and the middle is fixed")
    return out


def run() -> dict:
    s = inputs()
    nodes, members = truss(s)
    pu = pull_up(s, nodes, members)
    lg = lugs(s, nodes, members)
    cuts = cut_list(s, nodes, members, lg)
    rows = bom(s, cuts)
    return {"nodes": {k: v.tolist() for k, v in nodes.items()}, "pull_up": pu, "cuts": cuts, "bom": rows,
            "lugs": {k: [{**a, "dir": a["dir"].tolist()} for a in arms] for k, arms in lg.items()},
            "tube_mass_g": sum(r["mass_g"] for r in rows if r["mass_g"]),
            "nadir": nadir_flat(s), "joiner": joiner_fit(s), "flap": flap_split(s), "checks": checks(s, pu, cuts)}


def failed(res: dict) -> list[str]:
    return [c["name"] for c in res["checks"] if c["ok"] is False]


# ---- the report -------------------------------------------------------------------------------------------

def report(res: dict) -> str:
    s = inputs()
    pu = res["pull_up"]
    g = pu[pu["governing"]]
    mark = {True: "ok", False: "**FAIL**", None: "note"}
    L = ["# The sailplane: the centre wing's frame, its lugs and its cut list", "",
         "From `design/recon/sailplane.toml` by `osprey recon-sailplane`. Stations in mm: x aft from the nose, "
         "y to starboard, z up. Values marked REF in the design file are stand-ins.", "",
         "## Findings", "", "| Check | | |", "|---|---|---|"]
    L += [f"| {c['name']} | {mark[c['ok']]} | {c['text']} |" for c in res["checks"]]
    L += ["", f"## The pull-up: {s.loads.n:g} g, ultimate factor {s.loads.fs:g}", "",
          "All the lift on the wing, elliptic over the span, at stall x sqrt(n); the wing's own weight comes off "
          "where it is. The outer panels load the frame through the joiner box's two plates.", "",
          "| Case | Lift, N | Centre section, N | Each outer panel, N | Joiner shear, N | Joiner moment, N m | "
          "Couple on the plates, N | Each pylon, N | Tip of the frame, mm |", "|---|---|---|---|---|---|---|---|---|"]
    for c in CASES:
        r = pu[c]
        rz = [-v[2] for v in r["reactions_n"].values()]
        L.append(f"| {c}, {r['auw_kg']:g} kg | {r['lift_n']:.0f} | {r['center_lift_n']:.0f} | {r['panel_lift_n']:.0f} | "
                 f"{r['joiner_shear_n']:.0f} | {r['joiner_moment_nm']:.1f} | {r['joiner_couple_n']:.0f} | "
                 f"{min(rz):.0f} to {max(rz):.0f} | {r['tip_deflection_mm']:.1f} |")
    L += ["", f"The {pu['governing']} wings govern. The worst member of each kind, at limit load:", "",
          "| Members | Tube | Governing compression, N | on, mm | Critical, N | Buckling used | Most tension, N | "
          "Most bending, N m | Peak stress, MPa | Stress used |", "|---|---|---|---|---|---|---|---|---|---|"]
    for grp in dict.fromkeys(r["group"] for r in g["members"]):
        rows = [r for r in g["members"] if r["group"] == grp]
        c = min(rows, key=lambda r: r["axial_n"])
        wb, ws = max(rows, key=lambda r: r["u_buckle"]), max(rows, key=lambda r: r["u_stress"])
        tb = getattr(s.tube, rows[0]["tube"])
        c = wb if wb["u_buckle"] > 0 else c
        L.append(f"| {grp} | {tb.od_mm:g} x {tb.id_mm:g} | {max(-c['axial_n'], 0):.0f} | {wb['length_mm']:.0f} | "
                 f"{wb['pcr_n']:.0f} | {wb['u_buckle']:.2f} | {max(max(r['axial_n'] for r in rows), 0):.0f} | "
                 f"{max(r['moment_nmm'] for r in rows) / 1e3:.2f} | {ws['sigma_mpa']:.0f} | {ws['u_stress']:.2f} |")
    L += ["", "\"Used\" is the ultimate load over what the tube can take: above 1.00 it fails. Buckling is Euler, "
          "pinned between the member's ends.", ""]
    ch = max((r for r in g["members"] if r["group"] == "chord"), key=lambda r: r["u_buckle"])
    if ch["u_buckle"] > 1:
        E = s.carbon.e_gpa * 1e3
        need_i = s.loads.fs * -ch["axial_n"] * ch["length_mm"] ** 2 / (math.pi**2 * E)
        od = next(d for d in np.arange(s.tube.chord.od_mm, 40, 0.5)
                  if math.pi / 64 * (d**4 - (d - 2) ** 4) >= need_i)
        L += [f"The chord that buckles ({ch['name']}) carries {-ch['axial_n']:.0f} N over {ch['length_mm']:.0f} mm. "
              f"The same tube holds it braced every "
              f"{math.pi * math.sqrt(E * section(s.tube.chord)[1] / (s.loads.fs * -ch['axial_n'])):.0f} mm; "
              f"unbraced it takes a tube of {od:g} mm with a 1 mm wall. A skin bonded to the chords would brace "
              f"them, but the frame does not fit inside the skin as drawn.", ""]
    L += ["## Lugs", "", f"One printed {s.lug.material} lug at each of {len(res['lugs'])} nodes. Sockets are "
          f"{s.lug.socket_mm:g} mm deep with {s.lug.bond_gap_mm:g} mm of bond line on the radius and a "
          f"{s.lug.wall_mm:g} mm wall. A tube's seat is how far short of the node's centre it stops:", "",
          "| Members | Seat at each end, mm |", "|---|---|"]
    seats: dict[str, set] = {}
    for c in res["cuts"]:
        if "seats_mm" in c:
            seats.setdefault(c["group"], set()).add(" and ".join(f"{v:g}" for v in sorted(c["seats_mm"])))
    L += [f"| {k} | {'; '.join(sorted(v))} |" for k, v in seats.items()]
    L += ["", "## Cut list", "", "| Item | Stock | Qty | Cut, mm | Mass, g | |", "|---|---|---|---|---|---|"]
    for r in res["bom"]:
        L.append(f"| {r['item']} | {r['stock']} | {r['qty']} | {r['cut_mm']:.1f} | "
                 f"{'' if r['mass_g'] is None else format(r['mass_g'], '.0f')} | {r['note']} |")
    L += ["", f"Carbon tube in the frame: {res['tube_mass_g']:.0f} g. `cutlist.csv` lists every tube by its nodes.", ""]
    return "\n".join(L)


# ---- OpenSCAD ---------------------------------------------------------------------------------------------

def _scad(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (list, tuple, np.ndarray)):
        return "[" + ", ".join(_scad(x) for x in v) + "]"
    return f"{float(v):.6f}".rstrip("0").rstrip(".")


def params_scad(s, res: dict) -> str:
    """params.scad: every number the OpenSCAD modules use, from the design file and this module's results."""
    f, w, t, j, nd, lg, fl, fa = s.fuselage, s.wing, s.truss, s.joiner, s.nadir, s.lug, s.flap, s.fairing
    pts, _, lo = airfoil(w.airfoil)
    nf, fs_, jf = res["nadir"], res["flap"], res["joiner"]
    yo, yi = joiner_plates(s)
    nodes = res["nodes"]
    v = {
        "L": f.length_mm, "R": f.radius_mm, "nose_len": f.nose_mm, "mid_len": f.mid_mm, "nose_exp": f.nose_exp,
        "tail_angle": f.tail_angle_deg, "r_spinner": f.spinner_r_mm, "x_max": f.truncate_mm, "shell_t": f.wall_mm,
        "hatch_x": f.hatch_mm, "hatch_half_w": f.hatch_half_w_mm, "hatch_z": f.hatch_z_mm,
        "bulkheads": [[b.x_mm, b.t_mm, b.web_mm] for b in s.bulkhead],
        "rail_y": s.rails.y_mm, "rail_z": s.rails.z_mm, "rail_x": s.rails.x_mm, "rail_s": s.rails.section_mm,
        "center_span": w.center_span_mm, "chord": w.chord_mm, "le_x": w.le_x_mm, "chord_z": w.chord_z_mm,
        "skin_t": w.skin_mm, "rib_t": w.rib_mm, "dihedral": w.dihedral_deg,
        "airfoil_pts": pts[:-1], "lower_tab": lo,
        "flap_frac": fl.chord_frac, "flap_gap": fl.gap_mm, "flap_y0": fs_["inboard_y_mm"], "flap_end_gap": fl.end_gap_mm,
        "hinges_per_flap": fl.hinges_per_flap, "hinge_pocket": fl.hinge_pocket_mm, "hinge_z": fs_["hinge_z_mm"],
        "fair_half_w": fa.half_w_mm, "fair_fillet": fa.fillet_mm, "fair_step": fa.step_mm,
        "truss_x": [t.x_front_mm, t.x_rear_mm], "truss_z": [t.z_bot_mm, t.z_top_mm],
        "station_y": sorted({p[1] for k, p in nodes.items() if k in res["lugs"] and abs(p[1]) != t.pylon_y_mm}),
        "od_chord": s.tube.chord.od_mm, "od_strut": s.tube.strut.od_mm,
        "socket": lg.socket_mm, "bond_gap": lg.bond_gap_mm, "lug_wall": lg.wall_mm, "groove": lg.groove_mm,
        "grooves": lg.grooves, "port_d": lg.port_mm,
        "members": [[nodes[m["a"]], nodes[m["b"]], getattr(s.tube, m["tube"]).od_mm]
                    for m in res["pull_up"]["day"]["members"]],
        "lugs": [[k, nodes[k], [[a["dir"], a["od"], a["seat"], a["kind"]] for a in arms]]
                 for k, arms in res["lugs"].items()],
        "joiner_size": j.size_mm, "joiner_gap": j.gap_mm, "joiner_wall": j.wall_mm, "joiner_engage": j.engage_mm,
        "joiner_x": j.x_mm, "joiner_z": jf["z_mm"], "joiner_plate_t": j.plate_mm, "joiner_plate_y": [yo, yi],
        "joiner_margin": j.plate_margin_mm, "mpx": j.mpx_mm, "xt30": j.xt30_mm, "connector_x": j.connector_x_mm,
        "shoulder": j.shoulder_mm,
        "nadir_window": nd.window_mm, "nadir_pane": nf["pane_mm"], "nadir_pane_t": nd.pane_mm,
        "nadir_floor": nd.floor_mm, "nadir_xa": nf["xa_mm"], "nadir_za": nf["za_mm"], "nadir_tilt": nf["tilt_deg"],
        "nadir_margin": nd.margin_mm, "nadir_mount": nd.mount_mm, "nadir_boss": nd.boss_mm, "nadir_m3": nd.m3_mm,
    }
    head = ("// Written by `osprey recon-sailplane` from design/recon/sailplane.toml: do not edit, change the design "
            "file.\n// mm. Origin at the nose tip; +x aft, +y starboard, +z up.\n")
    return head + "".join(f"{k} = {_scad(x)};\n" for k, x in v.items())


def export(res: dict, out: Path) -> list[Path]:
    """The OpenSCAD parts, params.scad beside them, and the cut list as CSV."""
    s = inputs()
    d = out / "scad"
    d.mkdir(parents=True, exist_ok=True)
    files = []
    for src in sorted(SCAD.glob("*.scad")):
        files.append(Path(shutil.copy(src, d / src.name)))
    (d / "params.scad").write_text(params_scad(s, res))
    with open(out / "cutlist.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["part", "group", "tube", "cut_mm", "seat_a_mm", "seat_b_mm"])
        for c in res["cuts"]:
            wr.writerow((c["part"], c["group"], c["tube"], f"{c['cut_mm']:.1f}", *(f"{v:g}" for v in c.get("seats_mm", []))))
    return files + [d / "params.scad", out / "cutlist.csv"]
