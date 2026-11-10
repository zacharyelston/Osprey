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
- battery endurance >= mission time plus reserve;
- for a lifting body, the battery fitting inside the wing.

A tandem (the tilt-wing loiter craft) is two lifting surfaces, front and
rear, sized together: OpenAeroStruct's vortex lattice sees both, each has its
own spar, and the craft is trimmed and kept stable between them.

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
from osprey.recon import tailsitter
from osprey.recon.flight import G, rho
from osprey.recon.params import payload_kg, payload_w

MU_AIR = 1.8e-5
SKIN_WETTED = 2.04          # wetted area of a ~12 % section per unit planform area


def bwb(p) -> bool:
    """Tailless: the blended wing body or the crescent flying wing."""
    return getattr(p.layout, "kind", "twinboom") in ("bwb", "crescent")


def crescent(p) -> bool:
    return getattr(p.layout, "kind", "twinboom") == "crescent"


def tandem(p) -> bool:
    """Two lifting surfaces, front and rear: the tilt-body loiter craft."""
    return getattr(p.layout, "kind", "twinboom") == "tandem"


def trimmed(p) -> bool:
    """No tail to trim it: the flying wings and the tandem trim and keep a static margin themselves."""
    return bwb(p) or tandem(p)


def surfaces(p) -> list[dict]:
    """The lifting surfaces OpenAeroStruct sizes: one wing, or a tandem's front and rear."""
    if not tandem(p):
        return [surface(p)]
    out = []
    for name, w, off in (("front", p.wing, [0.0, 0.0, 0.0]), ("rear", p.rear, [p.rear.x_m, 0.0, p.rear.z_m])):
        mesh = generate_mesh({"num_y": p.wing.num_y, "num_x": p.wing.num_x, "wing_type": "rect", "symmetry": True,
                              "span": w.span_m, "root_chord": w.root_chord_m, "offset": np.array(off)})
        out.append({**_surface_common(p, mesh), "name": name, "span": w.span_m, "chord_cp": np.ones(2),
                    "twist_cp": np.zeros(2), "t_over_c_cp": np.array([w.t_over_c])})
    return out


def surface(p) -> dict:
    w, sp = p.wing, p.spar
    mesh = generate_mesh({"num_y": w.num_y, "num_x": w.num_x, "wing_type": "rect", "symmetry": True,
                          "span": w.span_m, "root_chord": w.root_chord_m})
    if bwb(p):
        # Swept, tailless, a thick centre body: chord, twist and thickness vary tip to root.
        surf = {**_surface_common(p, mesh), "sweep": w.sweep_deg, "chord_cp": np.array(w.chord_cp_init, float),
                "twist_cp": np.zeros(len(w.chord_cp_init)), "t_over_c_cp": np.array(w.t_over_c_cp, float)}
        if crescent(p):
            # The leading edge's curve and the tips' upsweep, point by point along the span.
            surf.update(xshear_cp=np.array(w.xshear_cp_init, float), zshear_cp=np.array(w.zshear_cp, float))
        return surf
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
    out = {"task": task, "wind_ms": m.wind_kn * KN, "boat_ms": m.boat_speed_kn * KN,
           "dist_m": float(np.linalg.norm(task.where(0.0))), "task_m": task.track_m,
           "boat_mode": getattr(m, "boat_mode", "sail")}
    if task.kind == "escort":
        out.update(task_s=task.duration, dist_m=task.r)                # a time on station, round the boat
    return out


def _chords(mesh):
    c = mesh[-1, :, 0] - mesh[0, :, 0]
    y = mesh[0, :, 1]
    return c, y


def _half_area(c, y):
    half = np.sum((c[1:] + c[:-1]) / 2 * np.diff(y))
    return half if half.real >= 0 else -half             # not abs(): it would drop the complex step


class Mass(om.ExplicitComponent):
    """Printed shell and the fixed masses: everything but the spars. Each
    surface's area, root and tip chord; S is all of them together."""

    def initialize(self):
        self.options.declare("p")
        self.options.declare("shapes")                   # {surface name: mesh shape}

    def setup(self):
        n = len(self.options["shapes"])
        for name, shape in self.options["shapes"].items():
            self.add_input(f"{name}_mesh", shape=shape, units="m")
        self.add_input("battery_kg", 1.0, units="kg")
        self.add_output("W0", 1.0, units="kg")
        self.add_output("skin_kg", 0.1, units="kg")
        self.add_output("S", 0.5, units="m**2")
        self.add_output("root_chord", np.full(n, 0.2), units="m")
        self.add_output("tip_chord", np.full(n, 0.2), units="m")
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        p = self.options["p"]
        S = 0.0
        for k, name in enumerate(self.options["shapes"]):
            c, y = _chords(i[f"{name}_mesh"])
            S = S + 2 * _half_area(c, y)
            o["root_chord"][k], o["tip_chord"][k] = c[-1], c[0]
        areal = getattr(p.skin, "areal_kg_m2", None) or p.skin.wall_m * p.skin.density_kgm3
        skin = SKIN_WETTED * S * areal * (1 + p.skin.rib_fraction)
        o["S"], o["skin_kg"] = S, skin
        o["W0"] = (p.body.mass_kg + p.avionics.mass_kg + payload_kg(p) + p.propulsion.motor_kg
                   + i["battery_kg"] + skin)


class Room(om.ExplicitComponent):
    """A lifting body carries its battery inside the wing: the room left, in
    litres, once the battery and the fixed kit are in. The wing's inside is
    the section's area (0.685 t c for a NACA 4-digit) along the span, of
    which usable_frac is clear of the spar, ribs and hatches."""

    def initialize(self):
        self.options.declare("p")
        self.options.declare("shape")

    def setup(self):
        ny = self.options["shape"][1]
        self.add_input("mesh", shape=self.options["shape"], units="m")
        self.add_input("t_over_c", shape=ny - 1)
        self.add_input("battery_kg", 1.0, units="kg")
        self.add_output("inside_l", 10.0)
        self.add_output("room_l", 1.0)
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        v = self.options["p"].volume
        c, y = _chords(i["mesh"])
        c_el = (c[1:] + c[:-1]) / 2
        half = np.sum(0.685 * i["t_over_c"] * c_el**2 * np.diff(y))
        inside = 2e3 * (half if half.real >= 0 else -half)
        o["inside_l"] = inside
        o["room_l"] = v.usable_frac * inside - i["battery_kg"] / v.battery_kg_per_l - v.fixed_l


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


class TipBend(om.ExplicitComponent):
    """How far the tip bends up at the manoeuvre, as a fraction of the semi-span. A carbon tube at its
    stress limit on a long span bends far past what a linear beam (or a wing) can stand."""

    def initialize(self):
        self.options.declare("shape")

    def setup(self):
        ny = self.options["shape"][1]
        self.add_input("mesh", shape=self.options["shape"], units="m")
        self.add_input("disp", shape=(ny, 6))
        self.add_output("frac", 0.0)
        self.declare_partials("*", "*", method="cs")

    def compute(self, i, o):
        o["frac"] = i["disp"][0, 2] / (-i["mesh"][0, 0, 1])


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
        if tailsitter.vtol(p):
            e = e - tailsitter.hover_energy_j(p, i["mass"])          # the launch and landing hover
        o["endurance"] = e / o["power"]
        w, vb, d = mi["wind_ms"], mi["boat_ms"], mi["dist_m"]
        t_task = mi["task_m"] * v / (v**2 - w**2)                    # a closed pattern in wind
        t_out = d / (v - w)                                            # worst case: into the wind
        mode = mi["boat_mode"]
        if mi.get("task_s"):
            # Time on station is fixed, however fast it flies, and the boat comes along: out to the
            # station and back from it.
            t = mi["task_s"] + 2 * d / (v - w)
        elif mode in ("return", "approach"):
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
    surfs = surfaces(p)
    names = [sf["name"] for sf in surfs]
    mi = mission_inputs(p)
    w, sp, lim = p.wing, p.spar, p.limits
    prob = om.Problem(reports=False)
    m = prob.model
    iv = m.add_subsystem("iv", om.IndepVarComp(), promotes=["*"])
    alt = mi["task"].alt_m
    iv.add_output("v", getattr(lim, "search_speed_init_ms", 18.0), units="m/s")
    iv.add_output("alpha_s", 4.0, units="deg")
    iv.add_output("alpha_m", 10.0, units="deg")
    iv.add_output("rho", rho(alt), units="kg/m**3")
    iv.add_output("CT", 1e-9, units="1/s")
    iv.add_output("R", 1.0, units="m")
    iv.add_output("speed_of_sound", 340.0, units="m/s")
    iv.add_output("n_s", 1.0)
    iv.add_output("n_m", lim.load_factor)
    cg0 = np.zeros(3)
    if trimmed(p):
        cg0[0] = sum(p.stability.cg_x_bounds_m) / 2                # start the CG mid-window
    iv.add_output("empty_cg", cg0, units="m")
    iv.add_output("battery_kg", p.propulsion.battery_kg, units="kg")
    m.add_subsystem("flow", om.ExecComp(["re = rho * v / mu", "Mach = v / a"], re={"units": "1/m"},
                                        rho={"units": "kg/m**3"}, v={"units": "m/s"}, a={"units": "m/s"},
                                        mu={"val": MU_AIR, "units": "Pa*s"}),
                    promotes_inputs=["rho", "v", ("a", "speed_of_sound")], promotes_outputs=["re", "Mach"])
    for sf in surfs:
        m.add_subsystem(sf["name"], AerostructGeometry(surface=sf))
    m.add_subsystem("mass", Mass(p=p, shapes={sf["name"]: sf["mesh"].shape for sf in surfs}),
                    promotes_inputs=["battery_kg"], promotes_outputs=["W0"])
    for n in names:
        m.connect(f"{n}.mesh", f"mass.{n}_mesh")
    points = [("alpha_s", "n_s"), ("alpha_m", "n_m")]
    if trimmed(p):
        # A probe point a degree above the task point, for the static margin.
        m.add_subsystem("probe", om.ExecComp("alpha_p = alpha_s + d", alpha_p={"units": "deg"},
                                             alpha_s={"units": "deg"}, d={"val": p.stability.probe_alpha_deg,
                                                                          "units": "deg"}),
                        promotes_inputs=["alpha_s"], promotes_outputs=["alpha_p"])
        points.append(("alpha_p", "n_s"))
    v_man = getattr(lim, "manoeuvre_speed_ms", None)
    if v_man:
        # A slow bird can't pull its load factor at its search speed: the manoeuvre is at V_A instead.
        iv.add_output("v_m", v_man, units="m/s")
    for k, (a, n_) in enumerate(points):
        pt = f"AS_point_{k}"
        m.add_subsystem(pt, AerostructPoint(surfaces=surfs), promotes_inputs=[
            ("v", "v_m") if v_man and k == 1 else "v", ("alpha", a), ("Mach_number", "Mach"), "re", "rho", "CT",
            "R", "W0", "speed_of_sound", "empty_cg", ("load_factor", n_)])
        for n in names:
            com = f"{pt}.coupled.{n}"
            m.connect(f"{n}.local_stiff_transformed", f"{com}.local_stiff_transformed")
            m.connect(f"{n}.nodes", f"{com}.nodes")
            m.connect(f"{n}.mesh", f"{com}.mesh")
            m.connect(f"{n}.radius", f"{pt}.{n}_perf.radius")
            m.connect(f"{n}.thickness", f"{pt}.{n}_perf.thickness")
            m.connect(f"{n}.nodes", f"{pt}.{n}_perf.nodes")
            m.connect(f"{n}.cg_location", f"{pt}.total_perf.{n}_cg_location")
            m.connect(f"{n}.structural_mass", f"{pt}.total_perf.{n}_structural_mass")
            m.connect(f"{n}.t_over_c", f"{pt}.{n}_perf.t_over_c")
    ns_ = len(names)
    m.add_subsystem("re_tip", om.ExecComp("re = rho * v * c / mu", re={"units": None, "shape": ns_},
                                          rho={"units": "kg/m**3"}, v={"units": "m/s"},
                                          c={"units": "m", "shape": ns_}, mu={"val": MU_AIR, "units": "Pa*s"}),
                    promotes_inputs=["rho", "v"])
    m.connect("mass.tip_chord", "re_tip.c")
    for n, sf in zip(names, surfs):
        sname = "spar" if n == "wing" else f"spar_{n}"
        m.add_subsystem(sname, SparFit(p=p, shape=sf["mesh"].shape))
        m.connect(f"{n}.mesh", f"{sname}.mesh")
        m.connect(f"{n}.radius", f"{sname}.radius")
        m.connect(f"{n}.t_over_c", f"{sname}.t_over_c")
    if ns_ > 1:                                                    # before the total: subsystems run in order
        m.add_subsystem("spars", om.MuxComp(vec_size=ns_))
        m.spars.add_var("m", shape=(1,), axis=0, units="kg")
        for k, n in enumerate(names):
            m.connect(f"{n}.structural_mass", f"spars.m_{k}")
    m.add_subsystem("total", om.ExecComp("mass = W0 + sum(spar)", mass={"units": "kg"}, W0={"units": "kg"},
                                         spar={"units": "kg", "shape": ns_}), promotes_inputs=["W0"])
    m.connect("wing.structural_mass" if ns_ == 1 else "spars.m", "total.spar")
    m.add_subsystem("perf", Performance(p=p, mi=mi, time_factor=time_factor), promotes_inputs=["v", "battery_kg"])
    m.connect("AS_point_0.CL", "perf.CL")
    m.connect("AS_point_0.CD", "perf.CD")
    m.connect("mass.S", "perf.S")
    m.connect("total.mass", "perf.mass")

    for n in names:
        wn = p.rear if n == "rear" else w
        m.add_design_var(f"{n}.geometry.span", *wn.span_bounds_m, units="m")
        m.add_design_var(f"{n}.geometry.chord_cp", *wn.chord_scale_bounds)
        if n == "front":
            # The front wing's root is the datum the angle of attack turns; the rear's twist is the decalage.
            m.add_design_var("front.twist_cp", -5.0, 8.0, units="deg", indices=[0])
        elif not bwb(p):
            m.add_design_var(f"{n}.twist_cp", -5.0, 8.0, units="deg")
        m.add_design_var(f"{n}.tube_group.radius_cp", *sp.radius_bounds_m, units="m", ref=0.01)
        m.add_design_var(f"{n}.thickness_cp", *sp.wall_bounds_m, units="m", ref=0.001)
        m.add_constraint(f"AS_point_1.{n}_perf.failure", upper=0.0)
        m.add_constraint(f"AS_point_1.{n}_perf.thickness_intersects", upper=0.0)
        m.add_constraint(f"{'spar' if n == 'wing' else 'spar_' + n}.fit", upper=0.0, ref=0.01)
        if getattr(lim, "tip_bend_max", None):
            sf_ = next(sf for sf in surfs if sf["name"] == n)
            m.add_subsystem(f"bend_{n}", TipBend(shape=sf_["mesh"].shape))
            m.connect(f"{n}.mesh", f"bend_{n}.mesh")
            m.connect(f"AS_point_1.coupled.{n}.disp", f"bend_{n}.disp")
            m.add_constraint(f"bend_{n}.frac", upper=lim.tip_bend_max, ref=0.1)
    if trimmed(p):
        st = p.stability
        if bwb(p):
            m.add_design_var("wing.twist_cp", *w.twist_bounds_deg, units="deg")
            if crescent(p):
                m.add_design_var("wing.geometry.xshear_cp", *w.xshear_bounds_m, units="m", ref=0.3)
            else:
                m.add_design_var("wing.sweep", *w.sweep_bounds_deg, units="deg", ref=20.0)
        m.add_design_var("empty_cg", lower=st.cg_x_bounds_m[0], upper=st.cg_x_bounds_m[1], indices=[0], units="m",
                         ref=0.2)
        m.add_constraint("AS_point_0.CM", indices=[1], equals=0.0, ref=0.05)            # trimmed
        m.add_subsystem("margin", om.ExecComp("sm = -(cm_p - cm_s) / (cl_p - cl_s)"))
        m.connect("AS_point_0.CM", "margin.cm_s", src_indices=[1])
        m.connect("AS_point_2.CM", "margin.cm_p", src_indices=[1])
        m.connect("AS_point_0.CL", "margin.cl_s")
        m.connect("AS_point_2.CL", "margin.cl_p")
        m.add_constraint("margin.sm", lower=st.static_margin_min, ref=0.1)
    if bwb(p):
        m.add_subsystem("depth", om.ExecComp("d = c * tc", d={"units": "m"}, c={"units": "m"},
                                             tc={"val": w.t_over_c_cp[-1]}))
        m.connect("mass.root_chord", "depth.c")
        if hasattr(p, "volume"):                                       # the payload lives in the wing
            m.add_constraint("depth.d", lower=p.volume.root_depth_min_m, units="m", ref=0.1)
            if hasattr(p.volume, "battery_kg_per_l"):                  # and so does the battery
                m.add_subsystem("room", Room(p=p, shape=surfs[0]["mesh"].shape), promotes_inputs=["battery_kg"])
                m.connect("wing.mesh", "room.mesh")
                m.connect("wing.t_over_c", "room.t_over_c")
                m.add_constraint("room.room_l", lower=0.0, ref=1.0)
    m.add_design_var("battery_kg", *p.propulsion.battery_bounds_kg, units="kg")
    m.add_design_var("v", *lim.search_speed_bounds_ms, units="m/s", ref=20.0)
    m.add_design_var("alpha_s", -5.0, 14.0, units="deg", ref=5.0)
    m.add_design_var("alpha_m", -5.0, 18.0, units="deg", ref=10.0)
    m.add_constraint("AS_point_0.L_equals_W", equals=0.0)
    m.add_constraint("AS_point_1.L_equals_W", equals=0.0)
    if getattr(getattr(p, "manufacture", None), "method", "printed") == "printed":
        diag = math.hypot(p.print.bed_m[0], p.print.bed_m[1]) - p.print.chord_margin_m
        m.add_constraint("mass.root_chord", upper=diag, units="m")
    m.add_constraint("perf.endurance_margin", lower=0.0)
    m.add_constraint("re_tip.re", lower=w.re_min, ref=1e5)
    m.add_subsystem("taper", om.ExecComp("gap = root - tip", gap={"units": "m", "shape": ns_},
                                         root={"units": "m", "shape": ns_}, tip={"units": "m", "shape": ns_}))
    m.connect("mass.root_chord", "taper.root")
    m.connect("mass.tip_chord", "taper.tip")
    m.add_constraint("taper.gap", lower=0.0, ref=0.1)              # no reverse taper: it stalls at the tips
    m.add_constraint("perf.v_stall", upper=lim.stall_speed_max_ms, units="m/s")
    m.add_constraint("perf.stall_margin", lower=0.0, ref=5.0)
    m.add_objective("total.mass", ref=3.0)
    prob.driver = om.ScipyOptimizeDriver(optimizer="SLSQP", tol=1e-6, maxiter=200, disp=False)
    prob.setup(force_alloc_complex=True)
    prob.set_solver_print(level=-1)
    if tandem(p):
        # Two coupled wings: give each point's aerostructural loop more room to settle.
        for k in range(len(points)):
            m._get_subsystem(f"AS_point_{k}.coupled").nonlinear_solver.options["maxiter"] = 300
    return prob, mi


def polar(prob, alphas=np.linspace(-2.0, 10.0, 7)) -> tuple[float, float]:
    """Fit CD = cd0 + k CL^2 to the optimized wing at the search point (the
    spar sized, the body drag added by the flight model, not here)."""
    a0 = float(prob.get_val("alpha_s", units="deg")[0])
    cl, cd = [], []
    for a in alphas:
        prob.set_val("alpha_s", a, units="deg")
        prob.run_model()
        cl.append(float(prob.get_val("AS_point_0.CL")[0]))
        cd.append(float(prob.get_val("AS_point_0.CD")[0]))
    prob.set_val("alpha_s", a0, units="deg")
    prob.run_model()
    A = np.stack([np.ones(len(cl)), np.square(cl)], 1)
    (cd0, k), *_ = np.linalg.lstsq(A, np.array(cd), rcond=None)
    return float(cd0), float(k)


def optimize(p, time_factor: float = 1.0) -> dict:
    """Run the sizing loop and return the design as plain numbers. If SLSQP
    fails, or steps somewhere the aerostructure can't solve, try again from
    the other starts (a heavier battery, faster): the tandem's two wings make
    a harder problem than one."""
    starts = [{}] + [{"battery_kg": b, "v": v} for b, v in ((0.5, 1.2), (0.8, 1.0))]
    for k, st in enumerate(starts):
        prob, mi = build(p, time_factor)
        lo, hi = p.propulsion.battery_bounds_kg
        if st:
            prob.set_val("battery_kg", lo + st["battery_kg"] * (hi - lo), units="kg")
            prob.set_val("v", st["v"] * float(prob.get_val("v", units="m/s")[0]), units="m/s")
        try:
            prob.run_model()
            fail = prob.run_driver()
        except Exception:
            if k == len(starts) - 1:
                raise
            continue
        ok = (bool(fail.success) if hasattr(fail, "success") else not fail) and _feasible(prob)
        if ok:
            break
    g = lambda n, u=None: np.atleast_1d(prob.get_val(n, units=u)).astype(float)
    first = "front" if tandem(p) else "wing"
    mesh = g(f"{first}.mesh")
    c, y = _chords(mesh.reshape(prob.get_val(f"{first}.mesh").shape))
    cd0_w, k = polar(prob)
    S = float(g("mass.S")[0])
    b = float(g(f"{first}.geometry.span", "m")[0])
    d = {
        "converged": bool(ok),
        "span_m": b, "S_m2": S, "aspect_ratio": b * b / S,
        "root_chord_m": float(c[-1]), "tip_chord_m": float(c[0]), "taper": float(c[0] / c[-1]),
        "re_tip": float(g("re_tip.re")[0]),
        "twist_deg": g(f"{first}.twist_cp", "deg").tolist(),
        "spar_radius_mm": (g(f"{first}.tube_group.radius_cp", "m") * 1e3).tolist(),
        "spar_wall_mm": (g(f"{first}.thickness_cp", "m") * 1e3).tolist(),
        "mass_total_kg": float(g("total.mass")[0]),
        "spar_kg": float(g("total.spar").sum()),
        "skin_kg": float(g("mass.skin_kg")[0]),
        "battery_kg": float(g("battery_kg")[0]),
        "fixed_kg": float(p.body.mass_kg + p.avionics.mass_kg + payload_kg(p) + p.propulsion.motor_kg),
        "payload": p.payload.layout,
        "v_search_ms": float(g("v")[0]),
        "CL": float(g("AS_point_0.CL")[0]),
        "CD_wing": float(g("AS_point_0.CD")[0]),
        "LD": float(g("perf.LD")[0]),
        "power_w": float(g("perf.power")[0]),
        "endurance_s": float(g("perf.endurance")[0]),
        "mission_time_s": float(g("perf.mission_time")[0]),
        "endurance_margin": float(g("perf.endurance_margin")[0]),
        "v_stall_ms": float(g("perf.v_stall")[0]),
        "failure": max(float(g(f"AS_point_1.{n}_perf.failure").max()) for n in _names(p)),
        "spar_fit_mm": max(float(g("spar.fit" if n == "wing" else f"spar_{n}.fit").max()) for n in _names(p)) * 1e3,
        "cd0": cd0_w + p.body.cda_m2 / S, "k": k,
        "kind": mi["task"].kind, "task_track_km": mi["task_m"] / 1e3,
        "half_span_y_m": (-y).tolist(), "chords_m": c.tolist(),
        "le_x_m": mesh.reshape(prob.get_val(f"{first}.mesh").shape)[0, :, 0].tolist(),
        "le_z_m": mesh.reshape(prob.get_val(f"{first}.mesh").shape)[0, :, 2].tolist(),
        "airframe": getattr(p.layout, "kind", "twinboom"),
        "float_kit": bool(p.water.kit_aboard),
    }
    if tailsitter.vtol(p):
        d.update(vtol=p.layout.vtol, hover_energy_wh=float(tailsitter.hover_energy_j(p, d["mass_total_kg"]) / 3600))
    if tailsitter.vtol(p) or scaled_motors(p):
        d.update(motor_kg=float(p.propulsion.motor_kg), motor_peak_w=float(p.propulsion.motor_peak_w))
    if tandem(p):
        # Each surface on its own: the renders and the sheet read these.
        d["surfaces"] = {}
        for n in _names(p):
            sh = prob.get_val(f"{n}.mesh").shape
            ms = g(f"{n}.mesh").reshape(sh)
            cn, yn = _chords(ms)
            bn = float(g(f"{n}.geometry.span", "m")[0])
            Sn = 2 * float(_half_area(cn, yn))
            d["surfaces"][n] = {"span_m": bn, "S_m2": Sn, "aspect_ratio": bn * bn / Sn, "root_chord_m": float(cn[-1]),
                                "tip_chord_m": float(cn[0]), "twist_deg": g(f"{n}.twist_cp", "deg").tolist(),
                                "spar_kg": float(g(f"{n}.structural_mass")[0]),
                                "spar_radius_mm": (g(f"{n}.tube_group.radius_cp", "m") * 1e3).tolist(),
                                "half_span_y_m": (-yn).tolist(), "chords_m": cn.tolist(),
                                "le_x_m": ms[0, :, 0].tolist(), "le_z_m": ms[0, :, 2].tolist(),
                                "CL": float(g(f"AS_point_0.{n}_perf.CL")[0])}
        d.update(span_m=max(s_["span_m"] for s_ in d["surfaces"].values()), cg_x_m=float(g("empty_cg", "m")[0]),
                 static_margin=float(g("margin.sm")[0]), cm_trim=float(g("AS_point_0.CM")[1]),
                 re_tip=float(g("re_tip.re").min()))
    if bwb(p):
        le = np.array(d["le_x_m"])
        d.update(sweep_deg=float(math.degrees(math.atan2(le[0] - le[-1], b / 2))), cg_x_m=float(g("empty_cg", "m")[0]),
                 static_margin=float(g("margin.sm")[0]), cm_trim=float(g("AS_point_0.CM")[1]),
                 t_over_c_cp=list(p.wing.t_over_c_cp), root_depth_m=float(g("depth.d")[0]))
        if hasattr(getattr(p, "volume", None), "battery_kg_per_l"):
            d.update(inside_l=float(g("room.inside_l")[0]), room_l=float(g("room.room_l")[0]),
                     battery_l=d["battery_kg"] / p.volume.battery_kg_per_l)
    d["time_factor"] = time_factor
    bed = p.print.bed_m
    molded = getattr(getattr(p, "manufacture", None), "method", "printed") == "molded"
    spans = [s_["span_m"] for s_ in d["surfaces"].values()] if tandem(p) else [b]
    d["print_panels"] = 0 if molded else sum(2 * math.ceil(bs / 2 / bed[2]) for bs in spans)
    d["print_chord_ok"] = molded or float(g("mass.root_chord").max()) <= math.hypot(bed[0], bed[1]) - p.print.chord_margin_m + 1e-6
    return d


def _feasible(prob, tol: float = 1e-3) -> bool:
    """Every constraint holds at the driver's answer: SLSQP can report success from a point that doesn't."""
    for name, meta in prob.model.get_constraints().items():
        v = np.atleast_1d(prob.get_val(meta["source"], units=meta.get("units"))).astype(float)
        if meta.get("indices") is not None:
            v = v.ravel()[meta["indices"].as_array()]
        ref = abs(meta.get("ref") or 1.0)
        if meta.get("equals") is not None and np.any(np.abs(v - meta["equals"]) > tol * ref):
            return False
        lo, hi = meta.get("lower"), meta.get("upper")
        if lo is not None and lo > -1e29 and np.any(v < lo - tol * ref):
            return False
        if hi is not None and hi < 1e29 and np.any(v > hi + tol * ref):
            return False
    return True


def _names(p) -> list[str]:
    return ["front", "rear"] if tandem(p) else ["wing"]


def scaled_motors(p) -> bool:
    """A motor sized from the take-off mass (W of peak shaft power per kg), not a fixed REF part."""
    return hasattr(p.propulsion, "w_per_kg")


def nacelle_floats(p, mass_kg: float) -> dict:
    """The tilt-wing's nacelle floats, sized to carry reserve x its weight between them, standing on
    them: each the nacelle's tail behind the trailing edge, a streamlined body of the given fineness;
    its skin mass and its drag (flat-plate friction on the wetted area with a body form factor), plus
    the motor end of the nacelle ahead of the wing."""
    nf = p.nacelle_floats
    vol = nf.reserve * mass_kg / p.water.density_kgm3 / nf.count
    dia = (4 * vol / (0.65 * math.pi * nf.fineness)) ** (1 / 3)           # prismatic coefficient 0.65
    length = nf.fineness * dia
    wet = 0.75 * math.pi * dia * length
    ff = 1 + 1.5 / nf.fineness**1.5 + 7 / nf.fineness**3
    return {"count": nf.count, "volume_l": vol * 1e3, "diameter_m": dia, "length_m": length, "drop_m": nf.drop_m,
            "kg": nf.count * (wet * nf.areal_kg_m2 + nf.fittings_kg),
            "cda_m2": nf.count * (nf.cf * ff * wet + nf.nose_cda_m2)}


def motors(p, mass_kg: float) -> tuple[float, float]:
    """Motor, ESC and prop mass (kg) and peak shaft power (W): from the hover for a VTOL, else from the mass."""
    if tailsitter.vtol(p):
        return tailsitter.motors(p, mass_kg)
    pr = p.propulsion
    peak = pr.w_per_kg * mass_kg
    return pr.kg_per_kw * peak / 1000 + pr.motor_fixed_kg, peak


def size_and_fly(p, iters: int = 6, tol: float = 0.03) -> tuple[dict, list[dict]]:
    """Size, fly with an unlimited battery, rescale the mission-time model by
    the energy the flight really used, and re-size, until they agree."""
    from dataclasses import replace

    from osprey.recon import flight

    factor, history = 1.0, []
    mass = None
    scaled = tailsitter.vtol(p) or scaled_motors(p)
    # Work the task to its goal: hours on station for a loiter, else up to six.
    on_station = getattr(p.mission, "escort_min", 0.0) * 60.0
    t_task = max(6 * 3600.0, on_station + 3600.0)
    floats = hasattr(p, "nacelle_floats")
    body = (p.body.mass_kg, p.body.cda_m2)
    for _ in range(iters):
        guess = mass or getattr(p.propulsion, "mass_guess_kg", 2.5)
        if scaled:
            # The motors follow the mass they have to lift: set them from the last sizing's mass.
            p.propulsion.motor_kg, p.propulsion.motor_peak_w = motors(p, guess)
        if floats:
            # So do the floats it lands on.
            nf = nacelle_floats(p, guess)
            p.body.mass_kg, p.body.cda_m2 = body[0] + nf["kg"], body[1] + nf["cda_m2"]
        d = optimize(p, factor)
        if floats:
            d["nacelle_floats"] = nf
        moved = mass is not None and abs(d["mass_total_kg"] - mass) / mass > 0.01
        mass = d["mass_total_kg"]
        ac = flight.Aircraft.from_design(p, d)
        big = replace(ac, energy_j=1e12)
        r = flight.simulate(p, big, t_max=t_task + 2 * 3600.0, task_time_max=t_task)
        used = 1e12 - float(r["energy"][-1])
        estimated = d["power_w"] * d["mission_time_s"] / factor
        new = max(used / estimated, 0.5)
        history.append({"time_factor": factor, "mass_kg": d["mass_total_kg"], "battery_kg": d["battery_kg"],
                        "flown_energy_wh": used / 3600, "estimated_energy_wh": estimated / 3600,
                        "flown_progress": float(r["progress"][-1]), "outcome": r["outcome"],
                        "flown_task_min": float((r["phase"] == "task").sum() * 0.5 / 60)})
        if abs(new - factor) / factor < tol and not ((scaled or floats) and (moved or len(history) < 2)):
            break
        factor = new
    return d, history
