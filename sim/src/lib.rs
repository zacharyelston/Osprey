//! Osprey's simulation loops. The Python package sets each sim up (designs, patterns, grids, tables) and
//! reads the results back; the time stepping is here. Each function takes plain dicts of numbers and
//! lists and returns one.

use std::collections::HashMap;

use pyo3::exceptions::{PyKeyError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;

pub mod aircraft;
pub mod cyclone;
pub mod flight;
pub mod num;
pub mod rotor;
pub mod tasks;
pub mod water;

use tasks::{Footprint, Grid, Kind, Sweep, Task, V2};

fn item<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<Bound<'py, PyAny>> {
    d.get_item(k)?
        .ok_or_else(|| PyKeyError::new_err(k.to_string()))
}

fn num(d: &Bound<'_, PyDict>, k: &str) -> PyResult<f64> {
    item(d, k)?.extract::<f64>()
}

fn list(d: &Bound<'_, PyDict>, k: &str) -> PyResult<Vec<f64>> {
    item(d, k)?.extract::<Vec<f64>>()
}

fn pair(d: &Bound<'_, PyDict>, k: &str) -> PyResult<V2> {
    let v = list(d, k)?;
    if v.len() != 2 {
        return Err(PyValueError::new_err(format!("{k}: want two numbers")));
    }
    Ok([v[0], v[1]])
}

fn points(d: &Bound<'_, PyDict>, k: &str) -> PyResult<Vec<V2>> {
    Ok(item(d, k)?
        .extract::<Vec<Vec<f64>>>()?
        .into_iter()
        .map(|p| [p[0], p[1]])
        .collect())
}

fn dict<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<Bound<'py, PyDict>> {
    Ok(item(d, k)?.cast_into::<PyDict>()?)
}

fn sweep(d: &Bound<'_, PyDict>) -> PyResult<Sweep> {
    let rects = item(d, "rects")?
        .extract::<Vec<Vec<f64>>>()?
        .into_iter()
        .map(|r| Footprint {
            a0: r[0],
            a1: r[1],
            c0: r[2],
            c1: r[3],
            q: r[4],
        })
        .collect();
    Ok(Sweep {
        along_m: num(d, "along_m")?,
        p_pass: num(d, "p_pass")?,
        rects,
    })
}

fn grid(d: &Bound<'_, PyDict>) -> PyResult<Grid> {
    Ok(Grid::new(
        list(d, "x")?,
        list(d, "y")?,
        list(d, "prior")?,
        list(d, "unfound")?,
        pair(d, "datum")?,
        pair(d, "drift")?,
        item(d, "nx")?.extract::<usize>()?,
    ))
}

fn task(d: &Bound<'_, PyDict>) -> PyResult<Task> {
    let kind: String = item(d, "kind")?.extract()?;
    let kind = match kind.as_str() {
        "search" => {
            let mut sweeps = HashMap::new();
            for (k, v) in dict(d, "sweeps")?.iter() {
                sweeps.insert(k.extract::<i64>()?, sweep(&v.cast_into::<PyDict>()?)?);
            }
            let patterns = item(d, "patterns")?
                .extract::<Vec<Vec<Vec<f64>>>>()?
                .into_iter()
                .map(|pat| pat.into_iter().map(|p| [p[0], p[1]]).collect())
                .collect();
            Kind::Search {
                datum0: pair(d, "datum0")?,
                patterns,
                spacing: num(d, "spacing")?,
                wp: 1,
                passes: 1,
                sweeps,
                grid: grid(&dict(d, "grid")?)?,
            }
        }
        "survey" => Kind::Survey {
            centre: pair(d, "centre")?,
            pattern: points(d, "pattern")?,
            wp: 0,
            finished: false,
            sweep: sweep(&dict(d, "sweep")?)?,
            grid: grid(&dict(d, "grid")?)?,
        },
        "inspect" => Kind::Inspect {
            v0: pair(d, "v0")?,
            vel: pair(d, "vel")?,
            r: num(d, "r")?,
            laps: num(d, "laps")?,
            swept: 0.0,
            theta: None,
        },
        "escort" => Kind::Escort {
            v0: pair(d, "v0")?,
            vel: pair(d, "vel")?,
            r: num(d, "r")?,
            duration: num(d, "duration")?,
            swept: 0.0,
            theta: None,
            t_on: None,
            t_now: 0.0,
        },
        other => return Err(PyValueError::new_err(format!("no task kind {other}"))),
    };
    Ok(Task {
        kind,
        alt_m: num(d, "alt_m")?,
        goal: num(d, "goal")?,
        drift: pair(d, "drift")?,
    })
}

/// The mission sim: ac (the aircraft), mission (wind, the boat, the rules), task (from the Python task's
/// spec()). Returns the record, the outcome and why it left the task, and the task's state at the end.
#[pyfunction]
fn flight_simulate<'py>(
    py: Python<'py>,
    ac: &Bound<'py, PyDict>,
    mission: &Bound<'py, PyDict>,
    task_spec: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let a = aircraft::Aircraft {
        mass_kg: num(ac, "mass_kg")?,
        s_m2: num(ac, "S_m2")?,
        cd0: num(ac, "cd0")?,
        k: num(ac, "k")?,
        cl_max: num(ac, "cl_max")?,
        eta_prop: num(ac, "eta_prop")?,
        eta_motor: num(ac, "eta_motor")?,
        p_aux_w: num(ac, "p_aux_w")?,
        energy_j: num(ac, "energy_j")?,
        p_shaft_max_w: num(ac, "p_shaft_max_w")?,
        v_search: num(ac, "v_search")?,
        bank_max_rad: num(ac, "bank_max_rad")?,
    };
    let mode: String = item(mission, "boat_mode")?.extract()?;
    let m = flight::Mission {
        wind: pair(mission, "wind")?,
        boat_v: pair(mission, "boat_v")?,
        boat_speed: num(mission, "boat_speed")?,
        boat_mode: match mode.as_str() {
            "return" | "approach" => flight::BoatMode::Toward,
            "hold" => flight::BoatMode::Hold,
            _ => flight::BoatMode::Sail,
        },
        cruise_alt_m: num(mission, "cruise_alt_m")?,
        reserve_frac: num(mission, "reserve_frac")?,
        recovery_radius_m: num(mission, "recovery_radius_m")?,
        t_cap: num(mission, "t_cap")?,
        dt: num(mission, "dt")?,
        t_max: num(mission, "t_max")?,
    };
    let mut tk = task(task_spec)?;
    let o = flight::simulate(&a, &m, &mut tk).map_err(PyValueError::new_err)?;
    let out = PyDict::new(py);
    let r = o.rec;
    out.set_item("t", r.t)?;
    out.set_item("x", r.x)?;
    out.set_item("y", r.y)?;
    out.set_item("h", r.h)?;
    out.set_item("v", r.v)?;
    out.set_item(
        "phase",
        r.phase.iter().map(|&p| p as u32).collect::<Vec<u32>>(),
    )?;
    out.set_item("energy", r.energy)?;
    out.set_item("progress", r.progress)?;
    out.set_item("power", r.power)?;
    out.set_item("bank", r.bank)?;
    out.set_item("boat_x", r.boat_x)?;
    out.set_item("boat_y", r.boat_y)?;
    out.set_item("outcome", o.phase)?;
    out.set_item("why", o.why)?;
    let st = PyDict::new(py);
    match tk.kind {
        Kind::Search {
            wp, passes, grid, ..
        } => {
            st.set_item("wp", wp)?;
            st.set_item("passes", passes)?;
            st.set_item("unfound", grid.unfound)?;
        }
        Kind::Survey {
            wp, finished, grid, ..
        } => {
            st.set_item("wp", wp)?;
            st.set_item("finished", finished)?;
            st.set_item("unfound", grid.unfound)?;
        }
        Kind::Inspect { swept, theta, .. } => {
            st.set_item("swept", swept)?;
            st.set_item("theta", theta)?;
        }
        Kind::Escort {
            swept,
            theta,
            t_on,
            t_now,
            ..
        } => {
            st.set_item("swept", swept)?;
            st.set_item("theta", theta)?;
            st.set_item("t_on", t_on)?;
            st.set_item("t_now", t_now)?;
        }
    }
    out.set_item("task", st)?;
    Ok(out)
}

/// A seaplane's take-off run on calm water at full power.
#[pyfunction]
fn takeoff<'py>(py: Python<'py>, c: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let k = water::Takeoff {
        mass_kg: num(c, "mass_kg")?,
        s_m2: num(c, "S_m2")?,
        v_lof: num(c, "v_lof")?,
        t0: num(c, "T0")?,
        cd: num(c, "cd")?,
        prop_efficiency: num(c, "prop_efficiency")?,
        motor_peak_w: num(c, "motor_peak_w")?,
        cl_run: num(c, "cl_run")?,
        r_hump: num(c, "r_hump")?,
        r_plane: num(c, "r_plane")?,
        hump_speed_frac: num(c, "hump_speed_frac")?,
        dt: num(c, "dt")?,
    };
    let o = water::takeoff(&k);
    let out = PyDict::new(py);
    out.set_item("v", o.v)?;
    out.set_item("x", o.x)?;
    out.set_item("t", o.t)?;
    out.set_item("worst", o.worst)?;
    out.set_item("at", o.at)?;
    Ok(out)
}

/// A tailsitter's launch from afloat to wing-borne.
#[pyfunction]
fn tailsitter_launch<'py>(py: Python<'py>, c: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let k = water::Launch {
        mass_kg: num(c, "mass_kg")?,
        t_max: num(c, "T_max")?,
        spool_s: num(c, "spool_s")?,
        rho_w: num(c, "rho_w")?,
        rs: list(c, "rs")?,
        vs: list(c, "Vs")?,
        ps: list(c, "Ps")?,
        surface_tension_npm: num(c, "surface_tension_npm")?,
        cd_pod: num(c, "cd_pod")?,
        end_area: num(c, "end_area")?,
        added_mass: num(c, "added_mass")?,
        climb_ms: num(c, "climb_ms")?,
        safe_height_m: num(c, "safe_height_m")?,
        s_m2: num(c, "S_m2")?,
        cla: num(c, "cla")?,
        a_stall: num(c, "a_stall")?,
        cl_max: num(c, "cl_max")?,
        cd0: num(c, "cd0")?,
        k: num(c, "k")?,
        v_wing: num(c, "v_wing")?,
        pitch_rate_rad_s: num(c, "pitch_rate_rad_s")?,
        prop_efficiency: num(c, "prop_efficiency")?,
        motor_peak_w: num(c, "motor_peak_w")?,
        dt: num(c, "dt")?,
    };
    let o = water::launch(&k);
    let out = PyDict::new(py);
    out.set_item("clear_s", o.clear_s)?;
    out.set_item("safe_s", o.safe_s)?;
    out.set_item("wing_borne_s", o.wing_borne_s)?;
    out.set_item("v_exit", o.v_exit)?;
    out.set_item("z_min", o.z_min)?;
    out.set_item("x", o.x)?;
    out.set_item("worst_tension", o.worst_tension)?;
    out.set_item(
        "track",
        o.track.iter().map(|p| p.to_vec()).collect::<Vec<_>>(),
    )?;
    Ok(out)
}

/// The Cyclone's spin-up from rest: the time it takes.
#[pyfunction]
fn cyclone_spin_up(c: &Bound<'_, PyDict>) -> PyResult<f64> {
    Ok(cyclone::spin_up(&cyclone::SpinUp {
        omega_h: num(c, "omega_h")?,
        radius_m: num(c, "R_m")?,
        inertia: num(c, "inertia")?,
        p_each_w: num(c, "p_each_w")?,
        f_static_n: num(c, "f_static_n")?,
        tip_prop_efficiency: num(c, "tip_prop_efficiency")?,
        k_drag: num(c, "k_drag")?,
        arms: num(c, "arms")?,
        dt: num(c, "dt")?,
    }))
}

/// The Cyclone's pitch-over (3->4) or pitch-up (4->1).
#[pyfunction]
fn cyclone_pitch<'py>(py: Python<'py>, c: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let o = cyclone::pitch(&cyclone::Pitch {
        lift: cyclone::Lift {
            prop_diameter_m: num(c, "prop_diameter_m")?,
            figure_of_merit: num(c, "figure_of_merit")?,
            induced_factor: num(c, "induced_factor")?,
        },
        s_m2: num(c, "S_m2")?,
        cl_max: num(c, "cl_max")?,
        cla: num(c, "cla")?,
        cd0: num(c, "cd0")?,
        k: num(c, "k")?,
        mass_kg: num(c, "mass_kg")?,
        v_wing: num(c, "v_wing")?,
        shaft_w: num(c, "shaft_w")?,
        props: num(c, "props")?,
        pitch_rate_rad_s: num(c, "pitch_rate_rad_s")?,
        motor_efficiency: num(c, "motor_efficiency")?,
        v0: num(c, "v0")?,
        up: item(c, "up")?.extract::<bool>()?,
        dt: num(c, "dt")?,
    });
    let out = PyDict::new(py);
    out.set_item("t", o.t)?;
    out.set_item("z_min", o.z_min)?;
    out.set_item("x", o.x)?;
    out.set_item("v", o.v)?;
    out.set_item("short_s", o.short_s)?;
    out.set_item("end_ratio", o.end_ratio)?;
    out.set_item("energy_j", o.energy_j)?;
    out.set_item("done", o.done)?;
    Ok(out)
}

fn blades(d: &Bound<'_, PyDict>) -> PyResult<rotor::Blades> {
    Ok(rotor::Blades {
        r: list(d, "r")?,
        dr: list(d, "dr")?,
        c: num(d, "c")?,
        n: num(d, "N")?,
        radius: num(d, "R")?,
        r0: num(d, "r0")?,
        rho: num(d, "rho")?,
        cla: num(d, "cla")?,
        cl_max: num(d, "cl_max")?,
        a_stall: num(d, "a_stall")?,
        blend: num(d, "blend")?,
        cd0: num(d, "cd0")?,
        kappa: num(d, "kappa")?,
    })
}

fn lift(c: &Bound<'_, PyDict>) -> PyResult<cyclone::Lift> {
    Ok(cyclone::Lift {
        prop_diameter_m: num(c, "prop_diameter_m")?,
        figure_of_merit: num(c, "figure_of_merit")?,
        induced_factor: num(c, "induced_factor")?,
    })
}

fn loads_dict<'py>(py: Python<'py>, ld: rotor::Loads) -> PyResult<Bound<'py, PyDict>> {
    let out = PyDict::new(py);
    out.set_item("T", ld.t)?;
    out.set_item("Tr", ld.tr)?;
    out.set_item("Q", ld.q)?;
    out.set_item("roll", ld.roll)?;
    out.set_item("pitch", ld.pitch)?;
    out.set_item("H", ld.h)?;
    out.set_item("alpha", ld.alpha)?;
    out.set_item("ut", ld.ut)?;
    Ok(out)
}

/// The Cyclone's arms' loads averaged over a turn (one evaluation).
#[pyfunction]
#[pyo3(signature = (bl, omega, theta, lam, v=0.0, a1=0.0, b1=0.0, n_psi=1))]
#[allow(clippy::too_many_arguments)]
fn rotor_loads<'py>(
    py: Python<'py>,
    bl: &Bound<'py, PyDict>,
    omega: f64,
    theta: f64,
    lam: Vec<f64>,
    v: f64,
    a1: f64,
    b1: f64,
    n_psi: usize,
) -> PyResult<Bound<'py, PyDict>> {
    let b = blades(bl)?;
    loads_dict(py, b.loads(omega, theta, &lam, v, a1, b1, n_psi))
}

/// The pitch that carries a weight at a spin rate: pitch, inflow ring by ring, and the loads there.
#[pyfunction]
fn rotor_hover<'py>(
    py: Python<'py>,
    bl: &Bound<'py, PyDict>,
    weight_n: f64,
    omega: f64,
) -> PyResult<Bound<'py, PyDict>> {
    let b = blades(bl)?;
    let (th, lam, ld) = b.hover(weight_n, omega);
    let out = PyDict::new(py);
    out.set_item("theta", th)?;
    out.set_item("lam", lam)?;
    out.set_item("loads", loads_dict(py, ld)?)?;
    Ok(out)
}

/// The spin building (1->2) or dying (2->1).
#[pyfunction]
fn rotor_transient<'py>(
    py: Python<'py>,
    bl: &Bound<'py, PyDict>,
    c: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let b = blades(bl)?;
    let rings = item(c, "rings")?
        .extract::<Vec<Vec<f64>>>()?
        .into_iter()
        .map(|g| rotor::Ring {
            r: g[0],
            n: g[1],
            p_each: g[2],
        })
        .collect();
    let k = rotor::Transient {
        lift: lift(c)?,
        tip_prop_efficiency: num(c, "tip_prop_efficiency")?,
        nacelle_cda: num(c, "nacelle_cda")?,
        rings,
        mass_kg: num(c, "mass_kg")?,
        inertia: num(c, "inertia")?,
        omega_h: num(c, "omega_h")?,
        theta_h: num(c, "theta_h")?,
        lam_h: list(c, "lam_h")?,
        b_rate_rad_s: num(c, "b_rate_rad_s")?,
        b_back_rad: num(c, "b_back_rad")?,
        spun_down_frac: num(c, "spun_down_frac")?,
        motor_efficiency: num(c, "motor_efficiency")?,
        build: item(c, "build")?.extract::<bool>()?,
        dt: num(c, "dt")?,
    };
    let o = rotor::transient(&b, &k);
    let out = PyDict::new(py);
    out.set_item("t", o.t)?;
    out.set_item("energy_j", o.energy_j)?;
    out.set_item("z", o.z)?;
    out.set_item("z_min", o.z_min)?;
    out.set_item("z_max", o.z_max)?;
    out.set_item("done", o.done)?;
    out.set_item("a_peak", o.a_peak)?;
    out.set_item(
        "track",
        o.track.iter().map(|p| p.to_vec()).collect::<Vec<_>>(),
    )?;
    Ok(out)
}

/// Mode 2 against the wind until it can't hold station: the rows it held, the limit, and why.
#[pyfunction]
fn rotor_wind_sweep<'py>(
    py: Python<'py>,
    bl: &Bound<'py, PyDict>,
    c: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let b = blades(bl)?;
    let k = rotor::Wind {
        omega: num(c, "omega")?,
        theta_h: num(c, "theta_h")?,
        lam_h: list(c, "lam_h")?,
        weight_n: num(c, "weight_n")?,
        hub_cda: num(c, "hub_cda")?,
        nacelle_cda: num(c, "nacelle_cda")?,
        tip_prop_efficiency: num(c, "tip_prop_efficiency")?,
        stall_deg: num(c, "stall_deg")?,
        swing_deg: num(c, "swing_deg")?,
        rating_w: num(c, "rating_w")?,
        v_max: num(c, "v_max")?,
        step: num(c, "step")?,
        n_psi: item(c, "n_psi")?.extract::<usize>()?,
    };
    let (rows, v2, why) = rotor::wind_sweep(&b, &k);
    let out = PyDict::new(py);
    let list_rows = pyo3::types::PyList::empty(py);
    for r in rows {
        let d = PyDict::new(py);
        d.set_item("v_ms", r.v)?;
        d.set_item("mu", r.mu)?;
        d.set_item("tilt_deg", r.tilt_deg)?;
        d.set_item("collective_deg", r.collective_deg)?;
        d.set_item("cyclic_deg", r.cyclic_deg)?;
        d.set_item("alpha_max_deg", r.alpha_max_deg)?;
        d.set_item("shaft_w", r.shaft_w)?;
        d.set_item("converged", r.converged)?;
        list_rows.append(d)?;
    }
    out.set_item("rows", list_rows)?;
    out.set_item("v_max_ms", v2)?;
    out.set_item("why", why)?;
    Ok(out)
}

/// The Cyclone lifting off the water: the time to clear it and the speed then.
#[pyfunction]
fn cyclone_water_launch<'py>(
    py: Python<'py>,
    c: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let (t, v) = rotor::water_launch(&rotor::WaterLaunch {
        thrust_n: num(c, "thrust_n")?,
        mass_kg: num(c, "mass_kg")?,
        rho_w: num(c, "rho_w")?,
        draft_m: num(c, "draft_m")?,
        zs: list(c, "zs")?,
        cum: list(c, "cum")?,
        tension_n: num(c, "tension_n")?,
        skin_cf: num(c, "skin_cf")?,
        wetted_per_m: num(c, "wetted_per_m")?,
        dt: num(c, "dt")?,
    });
    let out = PyDict::new(py);
    out.set_item("t", t)?;
    out.set_item("v", v)?;
    Ok(out)
}

#[pymodule]
fn osprey_sim(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(flight_simulate, m)?)?;
    m.add_function(wrap_pyfunction!(takeoff, m)?)?;
    m.add_function(wrap_pyfunction!(tailsitter_launch, m)?)?;
    m.add_function(wrap_pyfunction!(cyclone_spin_up, m)?)?;
    m.add_function(wrap_pyfunction!(cyclone_pitch, m)?)?;
    m.add_function(wrap_pyfunction!(rotor_loads, m)?)?;
    m.add_function(wrap_pyfunction!(rotor_hover, m)?)?;
    m.add_function(wrap_pyfunction!(rotor_transient, m)?)?;
    m.add_function(wrap_pyfunction!(rotor_wind_sweep, m)?)?;
    m.add_function(wrap_pyfunction!(cyclone_water_launch, m)?)?;
    Ok(())
}
