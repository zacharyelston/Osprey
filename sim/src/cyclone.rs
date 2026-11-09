//! The Cyclone's loops: the spin-up from rest (osprey.recon.cyclone.spin_up) and the pitch moves between
//! mode 4 and A pushing up (osprey.recon.cyclone_modes.pitch).

use crate::num::{rho, G};

pub struct SpinUp {
    pub omega_h: f64,
    pub radius_m: f64,
    pub inertia: f64,
    pub p_each_w: f64,
    pub f_static_n: f64,
    pub tip_prop_efficiency: f64,
    pub k_drag: f64,
    pub arms: f64,
    pub dt: f64,
}

/// From rest to the hover spin, motors at their peak: each tip prop's static thrust, falling away as
/// P / v as the tips speed up, against the arms' drag. The time it takes.
pub fn spin_up(k: &SpinUp) -> f64 {
    let (mut t, mut w) = (0.0f64, 0.0f64);
    while w < k.omega_h && t < 60.0 {
        let v = w * k.radius_m;
        let f = k
            .f_static_n
            .min(k.tip_prop_efficiency * k.p_each_w / v.max(1e-6));
        w += (k.arms * f * k.radius_m - k.k_drag * w * w) / k.inertia * k.dt;
        t += k.dt;
    }
    t
}

/// A (and A2) pushing along their axes, B centred: what osprey.recon.cyclone.lift_power gives.
#[derive(Clone, Copy)]
pub struct Lift {
    pub prop_diameter_m: f64,
    pub figure_of_merit: f64,
    pub induced_factor: f64,
}

impl Lift {
    /// Shaft power for a thrust with the air coming at u along the axes (no credit for descending).
    pub fn power(&self, thrust_n: f64, u: f64, props: f64) -> f64 {
        let area = props * std::f64::consts::PI * (self.prop_diameter_m / 2.0).powi(2);
        let vh = (thrust_n / (2.0 * rho(0.0) * area)).sqrt();
        let u = u.max(0.0);
        self.induced_factor * thrust_n * (u / 2.0 + (u * u / 4.0 + vh * vh).sqrt())
            + thrust_n * vh * (1.0 / self.figure_of_merit - self.induced_factor)
    }

    /// The thrust a shaft power gives with the air coming at u, by bisection.
    pub fn available(&self, shaft_w: f64, u: f64, props: f64) -> f64 {
        let (mut lo, mut hi) = (0.0f64, 200.0f64);
        for _ in 0..50 {
            let mid = (lo + hi) / 2.0;
            if self.power(mid, u, props) < shaft_w {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        lo
    }
}

pub struct Pitch {
    pub lift: Lift,
    pub s_m2: f64,
    pub cl_max: f64,
    pub cla: f64,
    pub cd0: f64,
    pub k: f64,
    pub mass_kg: f64,
    pub v_wing: f64,
    pub shaft_w: f64,
    pub props: f64,
    pub pitch_rate_rad_s: f64,
    pub motor_efficiency: f64,
    pub v0: f64,
    /// 3->4: the climb it starts the pitch-over in.
    pub vz0: f64,
    pub up: bool,
    pub dt: f64,
}

pub struct PitchOut {
    pub t: f64,
    pub z_min: f64,
    pub x: f64,
    pub v: f64,
    pub short_s: f64,
    pub end_ratio: f64,
    pub energy_j: f64,
    pub done: bool,
}

/// 3->4 (up = false): from A pushing up, moving at v0 and climbing at vz0, pitch over until wing-borne: A at
/// its burst throughout, tilted forward only as far as its thrust and the wing's growing lift still hold the
/// height (the climb let die away), no faster than the pitch rate; the rest of the thrust speeds it up. Done
/// at v_wing (1.2 times the stall), where the wing can take the weight and A throttles back to cruise. 4->1 (up = true): from level at v0, pitch up at the
/// pitch rate until A points up and the bird is down to a hover's drift, A pushing at what holds the height,
/// up to its burst. Where A can't hold it, it sinks. A 2-D point mass, a flat plate past the stall.
pub fn pitch(k: &Pitch) -> PitchOut {
    let a_stall = k.cl_max / k.cla;
    let mk = k.mass_kg;
    let w = mk * G;
    let lvl = 4.0f64.to_radians();
    let half_pi = std::f64::consts::FRAC_PI_2;
    let dt = k.dt;
    let mut theta = if k.up { lvl } else { half_pi };
    let (mut t, mut x, mut z, mut energy) = (0.0f64, 0.0f64, 0.0f64, 0.0f64);
    let (mut vx, mut vz) = (k.v0, if k.up { 0.0 } else { k.vz0 });
    let (mut z_min, mut short_s, mut end_ratio) = (0.0f64, 0.0f64, 0.0f64);
    let mut done = false;
    // The wing's lift and drag, and the lift's share upward, at a body angle, flying along gam at sp.
    let forces = |theta: f64, sp: f64, gam: f64| {
        let a = theta - gam;
        let cl = if a.abs() <= a_stall {
            k.cla * a
        } else {
            1.2 * a.sin() * a.cos()
        };
        let cd = k.cd0 + k.k * (cl * cl).min(k.cl_max * k.cl_max) + 1.2 * a.sin().powi(2);
        let q = 0.5 * rho(0.0) * sp * sp;
        let (lift, drag) = (q * k.s_m2 * cl, q * k.s_m2 * cd);
        (lift, drag, lift * gam.cos() - drag * gam.sin(), sp * a.cos())
    };
    while t < 40.0 {
        let sp = vx.hypot(vz);
        let gam = if sp > 0.1 { vz.atan2(vx) } else { theta };
        if k.up {
            theta = (theta + k.pitch_rate_rad_s * dt).min(half_pi);
        } else {
            let (_, _, lift_up, u) = forces(theta, sp, gam);
            let avail = k.lift.available(k.shaft_w, u, k.props);
            let need = (w - lift_up - mk * vz / 0.5) / avail.max(1e-9);
            let want = need.clamp(lvl.sin(), 1.0).asin();
            let step = k.pitch_rate_rad_s * dt;
            theta = want.clamp(theta - step, theta + step).clamp(lvl, half_pi);
        }
        let (lift, drag, lift_up, u) = forces(theta, sp, gam);
        let avail = k.lift.available(k.shaft_w, u, k.props);
        let hold = (w - lift_up - mk * vz / 0.5) / theta.sin().max(0.2);
        let thrust = if k.up { hold.max(0.0).min(avail) } else { avail };
        if hold > avail {
            short_s += dt;
        }
        end_ratio = if avail > 0.0 {
            w / avail
        } else {
            f64::INFINITY
        };
        vx += (thrust * theta.cos() - drag * gam.cos() - lift * gam.sin()) / mk * dt;
        vz += (thrust * theta.sin() - drag * gam.sin() + lift * gam.cos() - w) / mk * dt;
        x += vx * dt;
        z += vz * dt;
        z_min = z_min.min(z);
        energy += k.lift.power(thrust, u, k.props) / k.motor_efficiency * dt;
        t += dt;
        if k.up && theta >= half_pi - 1e-9 && sp < 2.0 {
            done = true;
            break;
        }
        if !k.up && sp >= k.v_wing && vz >= -0.5 {
            done = true;
            break;
        }
    }
    PitchOut {
        t,
        z_min,
        x,
        v: vx.hypot(vz),
        short_s,
        end_ratio,
        energy_j: energy,
        done,
    }
}
