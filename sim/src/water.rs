//! Off the water: a seaplane's take-off run (osprey.recon.water.takeoff) and a tailsitter's launch
//! (osprey.recon.tailsitter.launch).

use crate::num::{interp, rho, G};

pub struct Takeoff {
    pub mass_kg: f64,
    pub s_m2: f64,
    pub v_lof: f64,
    pub t0: f64,
    pub cd: f64,
    pub prop_efficiency: f64,
    pub motor_peak_w: f64,
    pub cl_run: f64,
    pub r_hump: f64,
    pub r_plane: f64,
    pub hump_speed_frac: f64,
    pub dt: f64,
}

/// Water resistance over weight on the water at u = speed / lift-off speed: up to the hump, then falling
/// away as the shoe climbs onto its step and planes.
fn resistance(k: &Takeoff, u: f64) -> f64 {
    if u <= k.hump_speed_frac {
        return k.r_hump * u / k.hump_speed_frac;
    }
    k.r_plane + (k.r_hump - k.r_plane) * (-(((u - k.hump_speed_frac) / 0.15).powi(2))).exp()
}

pub struct TakeoffOut {
    pub v: f64,
    pub x: f64,
    pub t: f64,
    pub worst: f64,
    pub at: f64,
}

/// A take-off run on calm water at full power.
pub fn takeoff(k: &Takeoff) -> TakeoffOut {
    let w = k.mass_kg * G;
    let rho0 = rho(0.0);
    let (mut v, mut x, mut t) = (0.0f64, 0.0, 0.0);
    let (mut worst, mut at) = (f64::INFINITY, 0.0);
    while v < k.v_lof && t < 120.0 {
        let q = 0.5 * rho0 * v * v;
        let thrust = k.t0.min(k.prop_efficiency * k.motor_peak_w / v.max(1e-3));
        let on_water = (w - q * k.s_m2 * k.cl_run).max(0.0);
        let net = thrust - q * k.s_m2 * k.cd - on_water * resistance(k, v / k.v_lof);
        if net / w < worst {
            worst = net / w;
            at = v;
        }
        if net <= 0.0 {
            break;
        }
        v += net / k.mass_kg * k.dt;
        x += v * k.dt;
        t += k.dt;
    }
    TakeoffOut { v, x, t, worst, at }
}

pub struct Launch {
    pub mass_kg: f64,
    pub t_max: f64,
    pub spool_s: f64,
    pub rho_w: f64,
    /// Volume in the water and waterline length as the bird rises from afloat.
    pub rs: Vec<f64>,
    pub vs: Vec<f64>,
    pub ps: Vec<f64>,
    pub surface_tension_npm: f64,
    pub cd_pod: f64,
    pub end_area: f64,
    pub added_mass: f64,
    pub climb_ms: f64,
    pub safe_height_m: f64,
    pub s_m2: f64,
    pub cla: f64,
    pub a_stall: f64,
    pub cl_max: f64,
    pub cd0: f64,
    pub k: f64,
    pub v_wing: f64,
    pub pitch_rate_rad_s: f64,
    pub prop_efficiency: f64,
    pub motor_peak_w: f64,
    pub dt: f64,
}

pub struct LaunchOut {
    pub clear_s: f64,
    pub safe_s: f64,
    pub wing_borne_s: f64,
    pub v_exit: f64,
    pub z_min: f64,
    pub x: f64,
    pub worst_tension: f64,
    /// (t, x, rise, pitch) every 0.05 s and at the end.
    pub track: Vec<[f64; 4]>,
}

/// Throttle up on the water, climb out, climb to the safe height, pitch over to wing-borne flight.
pub fn launch(k: &Launch) -> LaunchOut {
    let m = k.mass_kg;
    let w = m * G;
    let dt = k.dt;
    let top = *k.rs.last().unwrap();
    let (mut t, mut z, mut v) = (0.0f64, 0.0f64, 0.0f64);
    let mut worst_tension = 0.0f64;
    let mut track: Vec<[f64; 4]> = Vec::new();
    let half_pi = std::f64::consts::FRAC_PI_2;
    let mark = |track: &mut Vec<[f64; 4]>, t: f64, x: f64, z: f64, th: f64| {
        if track.is_empty() || t - track[track.len() - 1][0] >= 0.05 {
            track.push([t, x, z, th]);
        }
    };
    // 1. Out of the water: thrust spooling up; buoyancy, the pods' drag, the water they carry, surface tension.
    while z < top && t < 30.0 {
        let thrust = k.t_max * (t / k.spool_s).min(1.0);
        let vol = interp(z, &k.rs, &k.vs);
        let perim = interp(z, &k.rs, &k.ps);
        let tension = k.surface_tension_npm * perim;
        worst_tension = worst_tension.max(tension);
        let drag = if vol > 0.0 {
            0.5 * k.rho_w * k.cd_pod * k.end_area * v * v.abs()
        } else {
            0.0
        };
        let net = thrust + k.rho_w * G * vol - w - drag - if vol > 0.0 { tension } else { 0.0 };
        let m_eff = m + k.added_mass * k.rho_w * vol;
        v = (v + net / m_eff * dt).max(0.0);
        z += v * dt;
        t += dt;
        mark(&mut track, t, 0.0, z, half_pi);
    }
    let clear_s = t;
    let v_exit = v;
    // 2. Climb to the safe height, holding the climb speed.
    while z < top + k.safe_height_m && t < 60.0 {
        let thrust = k.t_max.min(w + m * (k.climb_ms - v) / 0.3);
        v += (thrust - w) / m * dt;
        z += v * dt;
        t += dt;
        mark(&mut track, t, 0.0, z, half_pi);
    }
    let safe_s = t;
    // 3. Pitch over at a set rate to the cruise attitude until wing-borne; a flat plate past the stall.
    let mut theta = half_pi;
    let theta_end = 4.0f64.to_radians();
    let (mut x, mut vx, mut vz) = (0.0f64, 0.0f64, v);
    let mut z_min = z;
    while t < 60.0 {
        theta = (theta - k.pitch_rate_rad_s * dt).max(theta_end);
        let sp = vx.hypot(vz);
        let gam = if sp > 0.1 { vz.atan2(vx) } else { half_pi };
        let a = theta - gam;
        let cl = if a.abs() <= k.a_stall {
            k.cla * a
        } else {
            1.2 * a.sin() * a.cos()
        };
        let cd = k.cd0 + k.k * (cl * cl).min(k.cl_max * k.cl_max) + 1.2 * a.sin().powi(2);
        let q = 0.5 * rho(z) * sp * sp;
        let (lift, drag) = (q * k.s_m2 * cl, q * k.s_m2 * cd);
        let lift_up = lift * gam.cos() - drag * gam.sin();
        let hold = (w - lift_up + m * (0.5 * k.climb_ms - vz) / 0.5) / theta.sin().max(0.2);
        let u = (sp * a.cos()).max(0.1);
        let t_avail = k.t_max.min(k.prop_efficiency * k.motor_peak_w / u);
        let thrust = hold.max(0.3 * w).min(t_avail);
        let ax = thrust * theta.cos() - drag * gam.cos() - lift * gam.sin();
        let az = thrust * theta.sin() - drag * gam.sin() + lift * gam.cos() - w;
        vx += ax / m * dt;
        vz += az / m * dt;
        x += vx * dt;
        z += vz * dt;
        z_min = z_min.min(z);
        t += dt;
        mark(&mut track, t, x, z, theta);
        if theta <= theta_end + 1e-9 && sp >= k.v_wing {
            break;
        }
    }
    track.push([t, x, z, theta]);
    LaunchOut {
        clear_s,
        safe_s,
        wing_borne_s: t,
        v_exit,
        z_min,
        x,
        worst_tension,
        track,
    }
}
