//! The 3-DOF point-mass mission sim (osprey.recon.flight.simulate): out to the task, work it, home to the
//! boat, on a wind triangle, bank-limited turns, a climb on the excess power and an energy budget.

use std::collections::HashMap;

use crate::aircraft::Aircraft;
use crate::num::{pyround, wrap, G};
use crate::tasks::{add, norm, scale, sub, Task, V2};

pub const OUTBOUND: u8 = 0;
pub const TASK: u8 = 1;
pub const RETURN: u8 = 2;
pub const RECOVERED: u8 = 3;
pub const LOST: u8 = 4;

/// What the boat does while the bird is away.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum BoatMode {
    /// Sails on.
    Sail,
    /// Heads for the task and heaves to near it, drifting with the water.
    Toward,
    /// Stays where it is, at anchor.
    Hold,
}

pub struct Mission {
    pub wind: V2,
    pub boat_v: V2,
    pub boat_speed: f64,
    pub boat_mode: BoatMode,
    pub cruise_alt_m: f64,
    pub reserve_frac: f64,
    pub recovery_radius_m: f64,
    pub t_cap: f64,
    pub dt: f64,
    pub t_max: f64,
}

#[derive(Default)]
pub struct Record {
    pub t: Vec<f64>,
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub h: Vec<f64>,
    pub v: Vec<f64>,
    pub phase: Vec<u8>,
    pub energy: Vec<f64>,
    pub progress: Vec<f64>,
    pub power: Vec<f64>,
    pub bank: Vec<f64>,
    pub boat_x: Vec<f64>,
    pub boat_y: Vec<f64>,
}

pub struct Outcome {
    pub rec: Record,
    pub phase: u8,
    pub why: String,
}

fn dot(a: V2, b: V2) -> f64 {
    a[0] * b[0] + a[1] * b[1]
}

pub fn simulate(ac: &Aircraft, m: &Mission, task: &mut Task) -> Result<Outcome, String> {
    let dt = m.dt;
    let wind = m.wind;
    let mut speeds: HashMap<(i64, i64), f64> = HashMap::new();
    let mut range_speed = |alt: f64, headwind: f64| -> f64 {
        let key = (pyround(alt / 10.0), pyround(headwind * 2.0));
        *speeds
            .entry(key)
            .or_insert_with(|| ac.best_range_speed(key.0 as f64 * 10.0, key.1 as f64 / 2.0))
    };
    let boat_vel = |task: &Task, t: f64, boat: V2| -> V2 {
        match m.boat_mode {
            BoatMode::Toward => {
                let to = sub(task.where_(t), boat);
                let dist = norm(to);
                if dist > 150.0 {
                    [m.boat_speed * to[0] / dist, m.boat_speed * to[1] / dist]
                } else {
                    task.drift
                }
            }
            BoatMode::Sail => m.boat_v,
            BoatMode::Hold => [0.0, 0.0],
        }
    };
    let mut boat: V2 = [0.0, 0.0];
    let mut pos: V2 = [0.0, 0.0];
    let e0 = task.entry(0.0, pos);
    let mut h = 2.0;
    let mut psi = e0[0].atan2(e0[1]);
    let mut energy = ac.energy_j;
    let mut phase = OUTBOUND;
    let mut t_task0 = 0.0;
    let mut why = String::from("-");
    let mut rec = Record::default();
    let mut t = 0.0;
    let mut target: V2 = [0.0, 0.0];
    let mut h_cmd = 0.0;
    while t < m.t_max && phase != RECOVERED && phase != LOST {
        if phase == OUTBOUND {
            target = task.entry(t, pos);
            let far = norm(sub(target, pos)) > 600.0;
            h_cmd = if far { m.cruise_alt_m } else { task.alt_m };
            if norm(sub(target, pos)) < 30.0 {
                phase = TASK;
                t_task0 = t;
            }
        }
        if phase == TASK {
            target = task.target(t, pos);
            h_cmd = task.alt_m;
            // Bingo: the energy to get home along the line to the boat as it is now, against that line's
            // headwind and the boat's own speed along it, plus the reserve.
            let to_boat = sub(boat, pos);
            let home = norm(to_boat);
            let hm = home.max(1e-6);
            let uh = [to_boat[0] / hm, to_boat[1] / hm];
            let head_home = -dot(wind, uh);
            let v_home = range_speed(m.cruise_alt_m, head_home);
            let away = dot(boat_vel(task, t, boat), uh);
            let t_home = home / (v_home - head_home - away).max(1.0);
            let bingo =
                ac.power(v_home, m.cruise_alt_m, 1.0, 0.0) * t_home * (1.0 + m.reserve_frac);
            let reason = task.done().or(if t - t_task0 > m.t_cap {
                Some("time")
            } else if energy <= bingo {
                Some("bingo")
            } else {
                None
            });
            if let Some(r) = reason {
                phase = RETURN;
                why = r.to_string();
            }
        }
        if phase == RETURN {
            target = boat;
            h_cmd = if norm(sub(boat, pos)) > 400.0 {
                m.cruise_alt_m
            } else {
                15.0
            };
            if norm(sub(boat, pos)) < m.recovery_radius_m {
                phase = RECOVERED;
                continue;
            }
        }

        // Speed: the task's on the task, the best range for the wind otherwise.
        let to = sub(target, pos);
        let dist = norm(to);
        let course = if dist > 1e-6 { to[0].atan2(to[1]) } else { psi };
        let u = [course.sin(), course.cos()];
        let head = -dot(wind, u);
        let v = if phase == TASK {
            ac.v_search
        } else {
            range_speed(h, head)
        };
        // The wind triangle: the air heading that makes good the course, crabbing into the cross wind.
        let cross = dot(wind, [u[1], -u[0]]);
        let psi_d = course - (cross / v).clamp(-1.0, 1.0).asin();
        let rate_max = G * ac.bank_max_rad.tan() / v;
        let dpsi = (-rate_max * dt).max((rate_max * dt).min(wrap(psi_d - psi)));
        psi = wrap(psi + dpsi);
        let bank = (v * (dpsi / dt) / G).atan();
        let n = 1.0 / bank.cos();
        let climb_max = ((ac.p_shaft_max_w * ac.eta_prop - ac.drag(v, h, n) * v) / ac.w()).max(0.0);
        let climb = (-3.0f64).max(climb_max.min((h_cmd - h) / 8.0));
        let pw = ac.power(v, h, n, climb);
        let vg = add(scale([psi.sin(), psi.cos()], v), wind);
        if phase == TASK && (h - task.alt_m).abs() < 15.0 {
            task.look(pos, vg[0].atan2(vg[1]), t, dt, norm(vg), h)?;
        }
        rec.t.push(t);
        rec.x.push(pos[0]);
        rec.y.push(pos[1]);
        rec.h.push(h);
        rec.v.push(v);
        rec.phase.push(phase);
        rec.energy.push(energy);
        rec.progress.push(task.progress());
        rec.power.push(pw);
        rec.bank.push(bank);
        rec.boat_x.push(boat[0]);
        rec.boat_y.push(boat[1]);
        pos = add(pos, scale(vg, dt));
        h = (h + climb * dt).max(0.0);
        boat = add(boat, scale(boat_vel(task, t, boat), dt));
        energy -= pw * dt;
        if energy <= 0.0 {
            phase = LOST;
        }
        t += dt;
    }
    Ok(Outcome { rec, phase, why })
}
