"""The Trident in MuJoCo, afloat: dropped at an angle in calm water, and riding regular waves ([sim] in
design/trident.toml).

MuJoCo has no free surface, so the water is ours. MuJoCo carries the rigid body: its mass, its inertia and the
integration. Each step we pose the sealed meshes (the envelope and the buoyant wing panels), clip them at the water's
surface, and apply the result through `xfrc_applied`:
- Buoyancy: the hydrostatic pressure under the surface, integrated over the wetted part. On calm water it is
  rho g V straight up at the centre of buoyancy, the same sum as the righting curves; in a wave the surface is
  curved and the pressure's slope pushes sideways too. The wave's pressure is not faded with depth (no Smith
  correction), which overstates the waves' push on the deep parts.
- Damping: a fraction of critical, in heave and in roll, from the stiffnesses upright, scaled by how much of the
  craft is wet; the heave part acts on the velocity of the centre of buoyancy through the water, the water moving
  with the wave's orbits. Added mass and wave radiation aren't modelled.
- The props are stopped: it is at rest afloat, not flying.

Body frame as in trident.py: z up the axis from the tail; the modules at 0, 120 and 240 degrees. The waves run
along world x.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from osprey import trident
from osprey.recon.puffin import _level, rot_y, rot_z

G = 9.81


def inputs() -> dict:
    return trident.inputs()["sim"]


# ---- the water ------------------------------------------------------------------------------------------------


class Waves:
    """A regular deep-water wave along world x, of height H and length L, ramped in over `ramp_s`."""

    def __init__(self, height_m: float = 0.0, length_m: float = 1.0, ramp_s: float = 0.0):
        self.a = height_m / 2
        self.k = 2 * math.pi / length_m
        self.w = math.sqrt(G * self.k)
        self.ramp = ramp_s
        self.period_s = 2 * math.pi / self.w

    def _amp(self, t: float) -> float:
        return self.a * (min(t / self.ramp, 1.0) if self.ramp > 0 else 1.0)

    def eta(self, x, t: float):
        return self._amp(t) * np.cos(self.k * x - self.w * t)

    def slope(self, x, t: float):
        return -self._amp(t) * self.k * np.sin(self.k * x - self.w * t)

    def orbit(self, x: float, z: float, t: float) -> np.ndarray:
        """The water's velocity at (x, z): the wave's orbit, fading with depth."""
        a = self._amp(t) * self.w * math.exp(self.k * min(z, 0.0))
        th = self.k * x - self.w * t
        return np.array([a * math.cos(th), 0.0, a * math.sin(th)])


def soup(meshes) -> np.ndarray:
    """Every sealed mesh's triangles as one (n, 3, 3) array."""
    return np.concatenate([v[f] for v, f in meshes])


def wetted(T: np.ndarray, eta: np.ndarray) -> tuple[float, np.ndarray]:
    """The volume of closed, outward-wound triangles below a surface z = eta (given at each vertex, (n, 3)), and
    its centroid.

    The divergence theorem with F = (0, 0, z - eta(x, y)): its divergence is 1 and it is zero on the surface, so the
    volume is the integral over the wetted skin of (z - eta) n_z dA, the surface itself adding nothing. With
    F = (0, 0, x (z - eta)), (0, 0, y (z - eta)) and (0, 0, (z^2 - eta^2) / 2) the same sum gives the first moments.
    Triangles that cross the surface are clipped where the height above it, interpolated along each edge, is zero."""
    P = np.concatenate([T, eta[..., None]], axis=2)          # x, y, z, eta at each vertex
    g = T[:, :, 2] - eta
    wet = g <= 0
    n = wet.sum(1)
    parts = [P[n == 3]]

    def cut(a, b, ga, gb):
        t = (ga / (ga - gb))[:, None]
        return a + (b - a) * t

    for count in (1, 2):
        sel = n == count
        if not sel.any():
            continue
        p, gg, w = P[sel], g[sel], wet[sel]
        lead = np.argmax(w if count == 1 else ~w, axis=1)      # the odd one out, first, the winding kept
        idx = (lead[:, None] + np.arange(3)) % 3
        p = np.take_along_axis(p, idx[:, :, None], 1)
        gg = np.take_along_axis(gg, idx, 1)
        p0, p1, p2 = p[:, 0], p[:, 1], p[:, 2]
        q01, q02 = cut(p0, p1, gg[:, 0], gg[:, 1]), cut(p0, p2, gg[:, 0], gg[:, 2])
        if count == 1:                                         # p0 wet: one triangle
            parts.append(np.stack([p0, q01, q02], 1))
        else:                                                  # p0 dry: the wet quad, two triangles
            parts += [np.stack([q01, p1, p2], 1), np.stack([q01, p2, q02], 1)]
    Q = np.concatenate(parts)
    if not len(Q):
        return 0.0, np.zeros(3)
    x, y, z, e = Q[:, :, 0], Q[:, :, 1], Q[:, :, 2], Q[:, :, 3]
    az = 0.5 * np.cross(Q[:, 1, :3] - Q[:, 0, :3], Q[:, 2, :3] - Q[:, 0, :3])[:, 2]
    gz = z - e

    def first(f):                                              # the integral of f (z - eta) n_z over the skin
        return float((az / 12 * ((f * gz).sum(1) + f.sum(1) * gz.sum(1))).sum())

    V = float((az * gz.mean(1)).sum())
    if V < 1e-9:
        return 0.0, np.zeros(3)
    return V, np.array([first(x), first(y), first((z + e) / 2)]) / V


# ---- the craft ------------------------------------------------------------------------------------------------


def inertia(r: dict) -> tuple[float, float]:
    """Moments of inertia about the CG (kg m^2): across (any axis square to the axis, by the three-fold symmetry)
    and about the axis. The modules' parts are rings of three at their radius; the core's walls a cylindrical shell,
    the battery a solid cylinder, everything else a lump 0.3 m round."""
    c, lay, zg = r["params"], r["layout"], r["zg_m"]
    ring = {"arm": lay["arm"], "wing": (lay["r_core"] + lay["r_tip"]) / 2, "tail": (c["bay_r_m"] + lay["r_tail"]) / 2}
    across = axial = 0.0
    for k, m in r["parts"].items():
        if m <= 0:
            continue
        dz = r["z"][k] - zg
        if k in trident.RADIAL:
            rr = ring[trident.RADIAL[k]]
            across += m * (rr**2 / 2 + dz**2)
            axial += m * rr**2
        elif k == "core walls":
            rc, L = lay["r_core"], lay["core_l"]
            across += m * (rc**2 / 2 + L**2 / 12 + dz**2)
            axial += m * rc**2
        elif k == "battery":
            rb, L = c["bay_r_m"], c["bay_m"]
            across += m * (rb**2 / 4 + L**2 / 12 + dz**2)
            axial += m * rb**2 / 2
        else:
            across += m * (0.3**2 + dz**2)
            axial += m * 0.3**2
    return across, axial


def mjcf(mass: float, zg: float, i_across: float, i_axial: float, dt: float) -> str:
    """One free rigid body, its frame at the tail on the axis, its mass at the CG. No contacts: the water is ours."""
    return f"""<mujoco model="trident-afloat">
  <option timestep="{dt}" integrator="RK4" gravity="0 0 {-G}"/>
  <worldbody>
    <body name="trident">
      <freejoint/>
      <inertial pos="0 0 {zg}" mass="{mass}" diaginertia="{i_across} {i_across} {i_axial}"/>
      <geom type="sphere" size="0.05" contype="0" conaffinity="0" mass="0"/>
    </body>
  </worldbody>
</mujoco>"""


def _quat(R: np.ndarray) -> np.ndarray:
    import mujoco

    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, R.reshape(-1))
    return q


class Afloat:
    """The Trident afloat in MuJoCo: the body, its sealed meshes, the water's forces and the damping."""

    def __init__(self, r: dict, sim: dict | None = None, waves: Waves | None = None):
        import mujoco

        self.sim = sim or inputs()
        self.r, c = r, r["params"]
        self.waves = waves or Waves()
        self.mass, self.zg = r["mass_kg"], r["zg_m"]
        self.rho = c["water_density_kgm3"]
        self.i_across, self.i_axial = inertia(r)
        self.model = mujoco.MjModel.from_xml_string(mjcf(self.mass, self.zg, self.i_across, self.i_axial,
                                                         self.sim["dt_s"]))
        self.data = mujoco.MjData(self.model)
        self.T = soup([m for _, m in trident.meshes(c)])
        lay = r["layout"]
        rim = [(lay["arm"] * math.cos(th) + c["prop_d_m"] / 2 * math.cos(a),
                lay["arm"] * math.sin(th) + c["prop_d_m"] / 2 * math.sin(a), lay["z_prop"])
               for th in trident.ANGLES for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
        self.rims = np.array(rim)
        self.need = self.mass / self.rho
        # Stiffnesses upright on calm water, for the damping: heave from the waterplane, roll from GM.
        cg = np.array([0.0, 0.0, self.zg])
        posed = [(v - cg, f) for _, (v, f) in trident.meshes(c)]
        h = _level(posed, self.need)
        Tc = soup(posed)
        dv = (wetted(Tc, np.full(Tc.shape[:2], h + 0.01))[0] - wetted(Tc, np.full(Tc.shape[:2], h - 0.01))[0]) / 0.02
        self.k_heave = self.rho * G * dv
        ms = [m for _, m in trident.meshes(c)]
        self.gm = trident.gz(ms, cg, self.need, math.radians(2)) / math.sin(math.radians(2))
        self.k_roll = self.mass * G * max(self.gm, 0.1)
        self.c_heave = 2 * self.sim["heave_damping"] * math.sqrt(self.k_heave * self.mass)
        self.c_roll = 2 * self.sim["roll_damping"] * math.sqrt(self.k_roll * self.i_across)
        self.roll_period_s = 2 * math.pi * math.sqrt(self.i_across / self.k_roll)
        self.heave_period_s = 2 * math.pi * math.sqrt(self.mass / self.k_heave)

    def place(self, phi: float, psi: float = 0.0):
        """At rest, knocked over by phi toward psi (as trident.gz), floating level at that angle."""
        R = rot_y(phi) @ rot_z(-psi)
        cg = np.array([0.0, 0.0, self.zg])
        c = self.r["params"]
        posed = [((v - cg) @ R.T, f) for _, (v, f) in trident.meshes(c)]
        h = _level(posed, self.need)
        cg_world = np.array([0.0, 0.0, -h])
        d = self.data
        d.qpos[:3] = cg_world - R @ cg
        d.qpos[3:7] = _quat(R)
        d.qvel[:] = 0.0
        d.time = 0.0
        import mujoco

        mujoco.mj_forward(self.model, d)

    def pose(self) -> tuple[np.ndarray, np.ndarray]:
        d = self.data
        return d.xmat[1].reshape(3, 3).copy(), d.xpos[1].copy()

    def tilt_deg(self) -> float:
        R, _ = self.pose()
        return math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))

    def forces(self) -> dict:
        """The water's force and torque on the body (world frame, about the CG), and what the step needs to know."""
        d, wv, t = self.data, self.waves, self.data.time
        R, o = self.pose()
        T = self.T @ R.T + o
        V, cb = wetted(T, wv.eta(T[:, :, 0], t))
        cg = d.xipos[1].copy()
        w_world = R @ d.qvel[3:6]
        out = {"V": V, "cb": cb, "cg": cg}
        if V <= 0:
            out["f"] = out["tau"] = np.zeros(3)
            return out
        s = wv.slope(cb[0], t)
        f = self.rho * G * V * np.array([-s, 0.0, 1.0])
        wet = min(V / self.need, 1.5)
        v_cb = d.qvel[:3] + np.cross(w_world, cb - o)
        rel = v_cb - wv.orbit(cb[0], cb[2], t)
        f = f - wet * self.c_heave * rel
        tau = np.cross(cb - cg, f)
        w_tilt = w_world - (w_world @ R[:, 2]) * R[:, 2]           # damp the rocking, not the spin about the axis
        tau = tau - wet * self.c_roll * w_tilt
        out["f"], out["tau"] = f, tau
        return out

    def step(self) -> dict:
        import mujoco

        fr = self.forces()
        self.data.xfrc_applied[1, :3] = fr["f"]
        self.data.xfrc_applied[1, 3:] = fr["tau"]
        mujoco.mj_step(self.model, self.data)
        return fr

    def clearances(self) -> tuple[float, float]:
        """The props' lowest rim point and the core's floor (its edge), above the water's surface."""
        R, o = self.pose()
        t = self.data.time
        p = self.rims @ R.T + o
        lay = self.r["layout"]
        fl = np.array([(lay["r_core"] * math.cos(a), lay["r_core"] * math.sin(a), lay["z_floor"])
                       for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]) @ R.T + o
        return (float((p[:, 2] - self.waves.eta(p[:, 0], t)).min()),
                float((fl[:, 2] - self.waves.eta(fl[:, 0], t)).min()))


# ---- the runs -------------------------------------------------------------------------------------------------


def craft(name: str) -> dict:
    """A craft to simulate: a layout, or "found" with a [hulls.*] build (`found+sandwich`)."""
    layout_name, _, hull = name.partition("+")
    build = {k: v for k, v in trident.inputs()["hulls"][hull].items() if k != "label"} if hull else {}
    return trident.size(layout_name, **build)


def drop(name: str, phi_deg: float, psi_deg: float, seconds: float, every: int = 10) -> dict:
    """Let go at rest, knocked over by phi toward psi, in calm water: the tilt over time, and when it settles."""
    sim = inputs()
    a = Afloat(craft(name), sim)
    a.place(math.radians(phi_deg), math.radians(psi_deg))
    n = int(seconds / sim["dt_s"])
    t, tilt = [], []
    for i in range(n):
        a.step()
        if i % every == 0:
            t.append(a.data.time)
            tilt.append(a.tilt_deg())
    tilt_a = np.array(tilt)
    up = tilt_a < sim["upright_deg"]
    settled = None
    if up[-1]:
        last_out = np.where(~up)[0]
        settled = float(t[last_out[-1] + 1]) if len(last_out) else 0.0
    first_up = next((k for k, u in enumerate(up) if u), None)
    over = float(tilt_a[first_up:].max()) if first_up is not None else None
    return {"craft": name, "phi_deg": phi_deg, "psi_deg": psi_deg, "t_s": t, "tilt_deg": tilt,
            "rights": bool(up[-1]), "settled_s": settled, "after_upright_max_deg": over,
            "end_tilt_deg": float(tilt_a[-1]), "roll_period_s": a.roll_period_s, "heave_period_s": a.heave_period_s,
            "gm_m": a.gm, "i_across": a.i_across, "i_axial": a.i_axial}


def ride(name: str, height_m: float, steepness: float, heading_deg: float, seconds: float) -> dict:
    """Upright at rest, a regular wave ramped in: the most it tilts, how close the props and the floor come to the
    water."""
    sim = inputs()
    wv = Waves(height_m, height_m / steepness, sim["ramp_s"])
    a = Afloat(craft(name), sim, wv)
    a.place(0.0)
    R0 = rot_z(math.radians(heading_deg))                       # the modules turned to the waves
    import mujoco

    a.data.qpos[3:7] = _quat(R0)
    a.data.qpos[:3] = R0 @ a.data.qpos[:3]
    mujoco.mj_forward(a.model, a.data)
    n = int(seconds / sim["dt_s"])
    tilt_max, props_min, floor_min, over30 = 0.0, math.inf, math.inf, 0
    trace_t, trace_tilt = [], []
    for i in range(n):
        a.step()
        if a.data.time < sim["ramp_s"]:
            continue
        tl = a.tilt_deg()
        tilt_max = max(tilt_max, tl)
        over30 += tl > 30
        if i % 5 == 0:
            p, f = a.clearances()
            props_min, floor_min = min(props_min, p), min(floor_min, f)
            trace_t.append(a.data.time)
            trace_tilt.append(tl)
    return {"craft": name, "height_m": height_m, "steepness": steepness, "length_m": height_m / steepness,
            "period_s": wv.period_s, "heading_deg": heading_deg, "tilt_max_deg": tilt_max,
            "over30_frac": over30 / max(n - int(sim["ramp_s"] / sim["dt_s"]), 1), "capsized": tilt_max > 90,
            "props_min_m": props_min, "floor_min_m": floor_min, "t_s": trace_t, "tilt_deg": trace_tilt}


def _job(args):
    kind, a = args
    return drop(*a) if kind == "drop" else ride(*a)


def run(workers: int = 0) -> dict:
    sim = inputs()
    jobs = [("drop", (c, p, d, sim["drop_s"])) for c in sim["drop_crafts"] for p in sim["drop_deg"]
            for d in sim["drop_dirs_deg"]]
    jobs += [("ride", (c, h, s, hd, sim["wave_s"])) for c in sim["wave_crafts"] for h in sim["wave_h_m"]
             for s in sim["wave_steepness"] for hd in sim["wave_heading_deg"]]
    if workers == 1:
        rows = [_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers or None) as ex:
            rows = list(ex.map(_job, jobs))
    nd = sum(1 for k, _ in jobs if k == "drop")
    return {"sim": sim, "drops": rows[:nd], "waves": rows[nd:]}


def _label(name: str) -> str:
    li = trident.inputs()
    layout_name, _, hull = name.partition("+")
    lab = li["layouts"][layout_name]["label"].split(":")[0]
    return f"{lab}, {li['hulls'][hull]['label'].split(',')[0].lower()}" if hull else lab


def report(res: dict) -> str:
    sim = res["sim"]
    lines = ["# The Trident in MuJoCo, afloat", "",
             "MuJoCo carries the rigid body; the water is ours: each step the sealed meshes are clipped at the "
             "surface and the pressure under it is summed into a force and a torque (`src/osprey/trident_sim.py`). "
             f"Damping is {sim['heave_damping'] * 100:.0f} % of critical in heave and {sim['roll_damping'] * 100:.0f} % "
             "in roll, both REF stand-ins; added mass, wave radiation and breaking waves aren't modelled. The props are "
             "stopped.", "",
             "## Dropped in calm water", "",
             f"Let go at rest, knocked over by each angle, in two directions: toward a module (0°) and between two (60°). "
             f"*Settles* is when it is last more than {sim['upright_deg']:g}° off upright; *swings to* is the most it "
             "tilts again after first coming upright.", "",
             "| Craft | GM | Roll period | Let go at | Toward | Comes back | Settles | Swings to |",
             "|---|---|---|---|---|---|---|---|"]
    for r in res["drops"]:
        lines.append(f"| {_label(r['craft'])} | {r['gm_m']:.1f} m | {r['roll_period_s']:.1f} s | {r['phi_deg']:.0f}° | "
                     f"{r['psi_deg']:.0f}° | {'yes' if r['rights'] else 'no: stays at %.0f°' % r['end_tilt_deg']} | "
                     + (f"{r['settled_s']:.1f} s" if r["settled_s"] is not None else "") + " | "
                     + (f"{r['after_upright_max_deg']:.0f}°" if r["after_upright_max_deg"] is not None else "") + " |")
    lines += ["", "## Riding regular waves", "",
              f"Upright at rest, a regular wave along x ramped in over {sim['ramp_s']:g} s, then {sim['wave_s']:g} s "
              "ridden. Steepness is height over length (1/7 breaks). Clearances are the lowest point of any prop's rim "
              "and of the core's floor edge above the local surface.", "",
              "| Craft | Height | Length | Period | Steepness | Heading | Most tilt | Over 30° | Props clear by "
              "| Floor clears by |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["waves"]:
        lines.append(f"| {_label(r['craft'])} | {r['height_m']:.1f} m | {r['length_m']:.0f} m | {r['period_s']:.1f} s | "
                     f"1/{1 / r['steepness']:.0f} | {r['heading_deg']:.0f}° | {r['tilt_max_deg']:.0f}°"
                     + (" capsized" if r["capsized"] else "") + f" | {r['over30_frac'] * 100:.0f} % | "
                     f"{r['props_min_m']:+.2f} m | {r['floor_min_m']:+.2f} m |")
    return "\n".join(lines) + "\n"
