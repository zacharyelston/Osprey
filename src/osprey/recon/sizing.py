"""Size the Recon airframe for a mission: OpenMDAO around OpenAeroStruct.

OpenAeroStruct couples a vortex-lattice wing with a carbon-tube spar beam at
two flight points:
- task: level flight at the task speed (searching, surveying or orbiting),
  which sets the drag;
- manoeuvre: load_factor g, which sets the spar.

Around it sit the parts OpenAeroStruct doesn't know:
- the printed shell's mass;
- the fixed masses: body, avionics, gimbal, motor;
- the battery;
- a mission time model:
  - transit out against the wind;
  - the task's track (a search plan, survey legs or orbits);
  - the return to the boat, wherever its boat_mode takes it.

SLSQP minimizes take-off mass subject to:
- lift = weight at both points;
- spar stress (OpenAeroStruct's failure check);
- the spar fitting inside the section;
- the chord fitting the printer bed;
- a chord Reynolds-number floor, and no reverse taper;
- stall speed for recovery on a moving boat;
- battery endurance >= mission time plus reserve.

The mission-time model is deliberately simple, so it is calibrated against
the 3-DOF flight sim (flight.py). size_and_fly() sizes, flies the design with
an unlimited battery to measure the energy the mission really takes, scales
the time model by flown / estimated, and re-sizes until the two agree. It
then flies the final design with its real battery as the check.
"""

from __future__ import annotations

import math

import numpy as np
import openmdao.api as om
from openaerostruct.meshing.mesh_generator import generate_mesh
from openaerostruct.integration.aerostruct_groups import AerostructGeometry, AerostructPoint

from osprey.motion import KN
from osprey.recon.flight import G, rho
from osprey.recon.params import payload_kg, payload_w

MU_AIR = 1.8e-5
SKIN_WETTED = 2.04          # wetted area of a ~12 % section per unit planform area


def bwb(p) -> bool:
    return getattr(p.layout, "kind", "twinboom") == "bwb"


def surface(p) -> dict:
    w, sp = p.wing, p.spar
    mesh = generate_mesh({"num_y": w.num_y, "num_x": w.num_x, "wing_type": "rect", "symmetry": True,
                          "span": w.span_m, "root_chord": w.root_chord_m})
    if bwb(p):
        # Swept, tailless, a thick centre body: chord, twist and thickness vary tip to root.
        return {**_surface_common(p, mesh), "sweep": w.sweep_deg, "chord_cp": np.array(w.chord_cp_init, float),
                "twist_cp": np.zeros(len(w.chord_cp_init)), "t_over_c_cp": np.array(w.t_over_c_cp, float)}
    return {**_surface_common(p, mesh), "chord_cp": np.ones(2), "twist_cp": np.zeros(2),
            "t_over_c_cp": np.array([w.t_over_c])}


def _surface_common(p, mesh) -> dict:
    w, sp = p.wing, p.spar
    return {
        "name": "wing", "symmetry": True, "S_ref_type": "projected", "fem_model_type": "tube", "mesh": mesh,
        "span": w.span_m,
        "radius_cp": np.full(2, sp.radius_m), "thickness_cp": np.full(2, sp.wall_m), "c_max_t": 0.30,
        "CL0": 0.0, "CD0": w.cd0_extra, "k_lam": w.k_lam, "with_viscous": True, "with_wave": False,
        "E": sp.E_pa, "G": sp.G_pa, "yield": sp.yield_pa / sp.safety_factor, "mrho": sp.density_kgm3,
        "fem_origin": w.fem_origin, "wing_weight_ratio": 1.0, "struct_weight_relief": True,
        "distributed_fuel_weight": False, "exact_failure_constraint": False,
    }


def mission_inputs(p) -> dict:
    """What the airframe-independent part of the mission asks for: how far
    away the task is, how much track it takes, the wind and the boat."""
    from osprey.recon import flight, tasks

    m = p.mission
    task = tasks.build(p, flight._wind(m))
    return {"task": task, "wind_ms": m.wind_kn * KN, "boat_ms": m.boat_speed_kn * KN,
            "dist_m": float(np.linalg.norm(task.where(0.0))), "task_m": task.track_m,
            "boat_mode": getattr(m, "boat_mode", "sail")}


def _chords(mesh):
    c = mesh[-1, :, 0] - mesh[0, :, 0]
    y = mesh[0, :, 1]
    return c, y


class Mass(om.ExplicitComponent):
    """Printed shell and the fixed masses: everything but the spar."""

    def initialize(self):
        self.options.declare("p")
        self.options.declare("shape")

    def setup(self):
        self.add_input("mesh", shape=self.options["shape"], units="m")
        self.add_input("battery_kg", 1.0, units="kg")
        self.add_output("W0", 1.0, units="kg")
        self.add_output("skin_kg", 0.1, units="kg")
        self.add_output("S", 0.5, units="m**2")
        self.add_output("root_chord", 0.2, units="m")
        self.add_output("tip_chord", 0.2, units="m")
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        p = self.options["p"]
        c, y = _chords(i["mesh"])
        half = np.sum((c[1:] + c[:-1]) / 2 * np.diff(y))
        S = 2 * (half if half.real >= 0 else -half)     # not abs(): it would drop the complex step
        areal = getattr(p.skin, "areal_kg_m2", None) or p.skin.wall_m * p.skin.density_kgm3
        skin = SKIN_WETTED * S * areal * (1 + p.skin.rib_fraction)
        o["S"], o["skin_kg"], o["root_chord"], o["tip_chord"] = S, skin, c[-1], c[0]
        o["W0"] = (p.body.mass_kg + p.avionics.mass_kg + payload_kg(p) + p.propulsion.motor_kg
                   + i["battery_kg"] + skin)


class SparFit(om.ExplicitComponent):
    """The tube plus clearance must fit inside the section: <= 0 at every element."""

    def initialize(self):
        self.options.declare("p")
        self.options.declare("shape")

    def setup(self):
        ny = self.options["shape"][1]
        self.add_input("mesh", shape=self.options["shape"], units="m")
        self.add_input("radius", shape=ny - 1, units="m")
        self.add_input("t_over_c", shape=ny - 1)
        self.add_output("fit", shape=ny - 1, units="m")
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        c, _ = _chords(i["mesh"])
        c_el = (c[1:] + c[:-1]) / 2
        o["fit"] = 2 * (i["radius"] + self.options["p"].spar.clearance_m) - i["t_over_c"] * c_el


class Performance(om.ExplicitComponent):
    """Search power, battery endurance, stall speeds and the mission's time."""

    def initialize(self):
        self.options.declare("p")
        self.options.declare("mi")
        self.options.declare("time_factor", 1.0)

    def setup(self):
        for n, v, u in [("CL", 0.5, None), ("CD", 0.03, None), ("S", 0.5, "m**2"), ("v", 18.0, "m/s"),
                        ("mass", 3.0, "kg"), ("battery_kg", 1.0, "kg")]:
            self.add_input(n, v, units=u)
        for n, u in [("power", "W"), ("endurance", "s"), ("mission_time", "s"), ("endurance_margin", None),
                     ("v_stall", "m/s"), ("stall_margin", "m/s"), ("LD", None)]:
            self.add_output(n, 1.0, units=u)
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        p, mi = self.options["p"], self.options["mi"]
        m, pr = p.mission, p.propulsion
        v, S = i["v"], i["S"]
        r = rho(mi["task"].alt_m)
        q = 0.5 * r * v**2
        D = q * S * i["CD"] + q * p.body.cda_m2
        aux = p.avionics.power_w + payload_w(p)
        o["power"] = D * v / (pr.prop_efficiency * pr.motor_efficiency) + aux
        o["LD"] = i["CL"] * S / (i["CD"] * S + p.body.cda_m2)
        e = i["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable
        o["endurance"] = e / o["power"]
        w, vb, d = mi["wind_ms"], mi["boat_ms"], mi["dist_m"]
        t_task = mi["task_m"] * v / (v**2 - w**2)                    # a closed pattern in wind
        t_out = d / (v - w)                                            # worst case: into the wind
        mode = mi["boat_mode"]
        if mode in ("return", "approach"):
            # The boat closes on the task while the drone works: home is d - vb T away.
            t = (t_task + t_out + d / (v - w)) / (1 + vb / (v - w))
        elif mode == "hold":
            t = t_task + t_out + d / (v - w)
        else:
            # Back to a boat that sailed on for the whole mission.
            t = (t_task + t_out + d / (v + w)) / (1 - vb / (v + w))
        t = t * self.options["time_factor"]
        o["mission_time"] = t
        o["endurance_margin"] = o["endurance"] / (t * (1 + m.reserve_frac)) - 1
        W = i["mass"] * G
        cl = p.wing.cl_max
        o["v_stall"] = (2 * W / (rho(0.0) * S * cl)) ** 0.5
        n = 1 / math.cos(math.radians(p.limits.bank_max_deg))
        o["stall_margin"] = v - p.limits.stall_margin * (2 * n * W / (r * S * cl)) ** 0.5


def build(p, time_factor: float = 1.0) -> tuple[om.Problem, dict]:
    surf = surface(p)
    mi = mission_inputs(p)
    shape = surf["mesh"].shape
    w, sp, lim = p.wing, p.spar, p.limits
    prob = om.Problem(reports=False)
    m = prob.model
    iv = m.add_subsystem("iv", om.IndepVarComp(), promotes=["*"])
    alt = mi["task"].alt_m
    iv.add_output("v", 18.0, units="m/s")
    iv.add_output("alpha_s", 4.0, units="deg")
    iv.add_output("alpha_m", 10.0, units="deg")
    iv.add_output("rho", rho(alt), units="kg/m**3")
    iv.add_output("CT", 1e-9, units="1/s")
    iv.add_output("R", 1.0, units="m")
    iv.add_output("speed_of_sound", 340.0, units="m/s")
    iv.add_output("n_s", 1.0)
    iv.add_output("n_m", lim.load_factor)
    cg0 = np.zeros(3)
    if bwb(p):
        cg0[0] = sum(p.stability.cg_x_bounds_m) / 2                # start the CG mid-window
    iv.add_output("empty_cg", cg0, units="m")
    iv.add_output("battery_kg", p.propulsion.battery_kg, units="kg")
    m.add_subsystem("flow", om.ExecComp(["re = rho * v / mu", "Mach = v / a"], re={"units": "1/m"},
                                        rho={"units": "kg/m**3"}, v={"units": "m/s"}, a={"units": "m/s"},
                                        mu={"val": MU_AIR, "units": "Pa*s"}),
                    promotes_inputs=["rho", "v", ("a", "speed_of_sound")], promotes_outputs=["re", "Mach"])
    m.add_subsystem("wing", AerostructGeometry(surface=surf))
    m.add_subsystem("mass", Mass(p=p, shape=shape), promotes_inputs=["battery_kg"], promotes_outputs=["W0"])
    m.connect("wing.mesh", "mass.mesh")
    points = [("alpha_s", "n_s"), ("alpha_m", "n_m")]
    if bwb(p):
        # A probe point a degree above the task point, for the static margin.
        m.add_subsystem("probe", om.ExecComp("alpha_p = alpha_s + d", alpha_p={"units": "deg"},
                                             alpha_s={"units": "deg"}, d={"val": p.stability.probe_alpha_deg,
                                                                          "units": "deg"}),
                        promotes_inputs=["alpha_s"], promotes_outputs=["alpha_p"])
        points.append(("alpha_p", "n_s"))
    for k, (a, n) in enumerate(points):
        pt = f"AS_point_{k}"
        m.add_subsystem(pt, AerostructPoint(surfaces=[surf]), promotes_inputs=[
            "v", ("alpha", a), ("Mach_number", "Mach"), "re", "rho", "CT", "R", "W0", "speed_of_sound",
            "empty_cg", ("load_factor", n)])
        com = f"{pt}.coupled.wing"
        m.connect("wing.local_stiff_transformed", f"{com}.local_stiff_transformed")
        m.connect("wing.nodes", f"{com}.nodes")
        m.connect("wing.mesh", f"{com}.mesh")
        m.connect("wing.radius", f"{pt}.wing_perf.radius")
        m.connect("wing.thickness", f"{pt}.wing_perf.thickness")
        m.connect("wing.nodes", f"{pt}.wing_perf.nodes")
        m.connect("wing.cg_location", f"{pt}.total_perf.wing_cg_location")
        m.connect("wing.structural_mass", f"{pt}.total_perf.wing_structural_mass")
        m.connect("wing.t_over_c", f"{pt}.wing_perf.t_over_c")
    m.add_subsystem("re_tip", om.ExecComp("re = rho * v * c / mu", re={"units": None}, rho={"units": "kg/m**3"},
                                          v={"units": "m/s"}, c={"units": "m"}, mu={"val": MU_AIR, "units": "Pa*s"}),
                    promotes_inputs=["rho", "v"])
    m.connect("mass.tip_chord", "re_tip.c")
    m.add_subsystem("spar", SparFit(p=p, shape=shape))
    m.connect("wing.mesh", "spar.mesh")
    m.connect("wing.radius", "spar.radius")
    m.connect("wing.t_over_c", "spar.t_over_c")
    m.add_subsystem("total", om.ExecComp("mass = W0 + spar", mass={"units": "kg"}, W0={"units": "kg"},
                                         spar={"units": "kg"}), promotes_inputs=["W0"])
    m.connect("wing.structural_mass", "total.spar")
    m.add_subsystem("perf", Performance(p=p, mi=mi, time_factor=time_factor), promotes_inputs=["v", "battery_kg"])
    m.connect("AS_point_0.wing_perf.CL", "perf.CL")
    m.connect("AS_point_0.wing_perf.CD", "perf.CD")
    m.connect("mass.S", "perf.S")
    m.connect("total.mass", "perf.mass")

    m.add_design_var("wing.geometry.span", *w.span_bounds_m, units="m")
    m.add_design_var("wing.geometry.chord_cp", *w.chord_scale_bounds)
    if bwb(p):
        st = p.stability
        m.add_design_var("wing.twist_cp", *w.twist_bounds_deg, units="deg")
        m.add_design_var("wing.sweep", *w.sweep_bounds_deg, units="deg", ref=20.0)
        m.add_design_var("empty_cg", lower=st.cg_x_bounds_m[0], upper=st.cg_x_bounds_m[1], indices=[0], units="m",
                         ref=0.2)
        m.add_constraint("AS_point_0.CM", indices=[1], equals=0.0, ref=0.05)            # trimmed
        m.add_subsystem("margin", om.ExecComp("sm = -(cm_p - cm_s) / (cl_p - cl_s)"))
        m.connect("AS_point_0.CM", "margin.cm_s", src_indices=[1])
        m.connect("AS_point_2.CM", "margin.cm_p", src_indices=[1])
        m.connect("AS_point_0.wing_perf.CL", "margin.cl_s")
        m.connect("AS_point_2.wing_perf.CL", "margin.cl_p")
        m.add_constraint("margin.sm", lower=st.static_margin_min, ref=0.1)
        m.add_subsystem("depth", om.ExecComp("d = c * tc", d={"units": "m"}, c={"units": "m"},
                                             tc={"val": w.t_over_c_cp[-1]}))
        m.connect("mass.root_chord", "depth.c")
        m.add_constraint("depth.d", lower=p.volume.root_depth_min_m, units="m", ref=0.1)
    else:
        m.add_design_var("wing.twist_cp", -5.0, 8.0, units="deg")
    m.add_design_var("wing.tube_group.radius_cp", *sp.radius_bounds_m, units="m", ref=0.01)
    m.add_design_var("wing.thickness_cp", *sp.wall_bounds_m, units="m", ref=0.001)
    m.add_design_var("battery_kg", *p.propulsion.battery_bounds_kg, units="kg")
    m.add_design_var("v", *lim.search_speed_bounds_ms, units="m/s", ref=20.0)
    m.add_design_var("alpha_s", -5.0, 14.0, units="deg", ref=5.0)
    m.add_design_var("alpha_m", -5.0, 18.0, units="deg", ref=10.0)
    m.add_constraint("AS_point_0.L_equals_W", equals=0.0)
    m.add_constraint("AS_point_1.L_equals_W", equals=0.0)
    m.add_constraint("AS_point_1.wing_perf.failure", upper=0.0)
    m.add_constraint("AS_point_1.wing_perf.thickness_intersects", upper=0.0)
    m.add_constraint("spar.fit", upper=0.0, ref=0.01)
    if getattr(getattr(p, "manufacture", None), "method", "printed") == "printed":
        diag = math.hypot(p.print.bed_m[0], p.print.bed_m[1]) - p.print.chord_margin_m
        m.add_constraint("mass.root_chord", upper=diag, units="m")
    m.add_constraint("perf.endurance_margin", lower=0.0)
    m.add_constraint("re_tip.re", lower=w.re_min, ref=1e5)
    m.add_subsystem("taper", om.ExecComp("gap = root - tip", gap={"units": "m"}, root={"units": "m"},
                                         tip={"units": "m"}))
    m.connect("mass.root_chord", "taper.root")
    m.connect("mass.tip_chord", "taper.tip")
    m.add_constraint("taper.gap", lower=0.0, ref=0.1)              # no reverse taper: it stalls at the tips
    m.add_constraint("perf.v_stall", upper=lim.stall_speed_max_ms, units="m/s")
    m.add_constraint("perf.stall_margin", lower=0.0, ref=5.0)
    m.add_objective("total.mass", ref=3.0)
    prob.driver = om.ScipyOptimizeDriver(optimizer="SLSQP", tol=1e-6, maxiter=200, disp=False)
    prob.setup(force_alloc_complex=True)
    prob.set_solver_print(level=-1)
    return prob, mi


def polar(prob, alphas=np.linspace(-2.0, 10.0, 7)) -> tuple[float, float]:
    """Fit CD = cd0 + k CL^2 to the optimized wing at the search point (the
    spar sized, the body drag added by the flight model, not here)."""
    a0 = float(prob.get_val("alpha_s", units="deg")[0])
    cl, cd = [], []
    for a in alphas:
        prob.set_val("alpha_s", a, units="deg")
        prob.run_model()
        cl.append(float(prob.get_val("AS_point_0.wing_perf.CL")[0]))
        cd.append(float(prob.get_val("AS_point_0.wing_perf.CD")[0]))
    prob.set_val("alpha_s", a0, units="deg")
    prob.run_model()
    A = np.stack([np.ones(len(cl)), np.square(cl)], 1)
    (cd0, k), *_ = np.linalg.lstsq(A, np.array(cd), rcond=None)
    return float(cd0), float(k)


def optimize(p, time_factor: float = 1.0) -> dict:
    """Run the sizing loop and return the design as plain numbers."""
    prob, mi = build(p, time_factor)
    prob.run_model()
    fail = prob.run_driver()
    ok = bool(fail.success) if hasattr(fail, "success") else not fail
    g = lambda n, u=None: np.atleast_1d(prob.get_val(n, units=u)).astype(float)
    mesh = g("wing.mesh")
    c, y = _chords(mesh.reshape(prob.get_val("wing.mesh").shape))
    cd0_w, k = polar(prob)
    S = float(g("mass.S")[0])
    b = float(g("wing.geometry.span", "m")[0])
    d = {
        "converged": bool(ok),
        "span_m": b, "S_m2": S, "aspect_ratio": b * b / S,
        "root_chord_m": float(c[-1]), "tip_chord_m": float(c[0]), "taper": float(c[0] / c[-1]),
        "re_tip": float(g("re_tip.re")[0]),
        "twist_deg": g("wing.twist_cp", "deg").tolist(),
        "spar_radius_mm": (g("wing.tube_group.radius_cp", "m") * 1e3).tolist(),
        "spar_wall_mm": (g("wing.thickness_cp", "m") * 1e3).tolist(),
        "mass_total_kg": float(g("total.mass")[0]),
        "spar_kg": float(g("wing.structural_mass")[0]),
        "skin_kg": float(g("mass.skin_kg")[0]),
        "battery_kg": float(g("battery_kg")[0]),
        "fixed_kg": float(p.body.mass_kg + p.avionics.mass_kg + payload_kg(p) + p.propulsion.motor_kg),
        "payload": p.payload.layout,
        "v_search_ms": float(g("v")[0]),
        "CL": float(g("AS_point_0.wing_perf.CL")[0]),
        "CD_wing": float(g("AS_point_0.wing_perf.CD")[0]),
        "LD": float(g("perf.LD")[0]),
        "power_w": float(g("perf.power")[0]),
        "endurance_s": float(g("perf.endurance")[0]),
        "mission_time_s": float(g("perf.mission_time")[0]),
        "endurance_margin": float(g("perf.endurance_margin")[0]),
        "v_stall_ms": float(g("perf.v_stall")[0]),
        "failure": float(g("AS_point_1.wing_perf.failure").max()),
        "spar_fit_mm": float(g("spar.fit").max() * 1e3),
        "cd0": cd0_w + p.body.cda_m2 / S, "k": k,
        "kind": mi["task"].kind, "task_track_km": mi["task_m"] / 1e3,
        "half_span_y_m": (-y).tolist(), "chords_m": c.tolist(),
        "le_x_m": mesh.reshape(prob.get_val("wing.mesh").shape)[0, :, 0].tolist(),
        "airframe": getattr(p.layout, "kind", "twinboom"),
    }
    if bwb(p):
        d.update(sweep_deg=float(g("wing.sweep", "deg")[0]), cg_x_m=float(g("empty_cg", "m")[0]),
                 static_margin=float(g("margin.sm")[0]), cm_trim=float(g("AS_point_0.CM")[1]),
                 t_over_c_cp=list(p.wing.t_over_c_cp), root_depth_m=float(g("depth.d")[0]))
    d["time_factor"] = time_factor
    bed = p.print.bed_m
    molded = getattr(getattr(p, "manufacture", None), "method", "printed") == "molded"
    d["print_panels"] = 0 if molded else 2 * math.ceil(b / 2 / bed[2])
    d["print_chord_ok"] = molded or d["root_chord_m"] <= math.hypot(bed[0], bed[1]) - p.print.chord_margin_m + 1e-6
    return d


def size_and_fly(p, iters: int = 6, tol: float = 0.03) -> tuple[dict, list[dict]]:
    """Size, fly with an unlimited battery, rescale the mission-time model by
    the energy the flight really used, and re-size, until they agree."""
    from dataclasses import replace

    from osprey.recon import flight

    factor, history = 1.0, []
    for _ in range(iters):
        d = optimize(p, factor)
        ac = flight.Aircraft.from_design(p, d)
        big = replace(ac, energy_j=1e12)
        r = flight.simulate(p, big, t_max=8 * 3600.0, task_time_max=6 * 3600.0)     # work the task to its goal
        used = 1e12 - float(r["energy"][-1])
        estimated = d["power_w"] * d["mission_time_s"] / factor
        new = max(used / estimated, 0.5)
        history.append({"time_factor": factor, "mass_kg": d["mass_total_kg"], "battery_kg": d["battery_kg"],
                        "flown_energy_wh": used / 3600, "estimated_energy_wh": estimated / 3600,
                        "flown_progress": float(r["progress"][-1]), "outcome": r["outcome"],
                        "flown_task_min": float((r["phase"] == "task").sum() * 0.5 / 60)})
        if abs(new - factor) / factor < tol:
            break
        factor = new
    return d, history
