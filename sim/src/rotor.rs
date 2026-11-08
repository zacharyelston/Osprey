//! The Cyclone's arms as rotor blades (osprey.recon.cyclone_dynamics): blade elements, the inflow ring by
//! ring, the hover trim, the spin building and dying, and the trim in an edgewise wind. The sums follow
//! NumPy's (pairwise along a row, row by row down a column) so the numbers match the Python they replace.

use crate::cyclone::Lift;
use crate::num::{pairwise_sum, pymod, rho};
use std::f64::consts::PI;

#[derive(Clone, Debug)]
pub struct Blades {
    pub r: Vec<f64>,
    pub dr: Vec<f64>,
    pub c: f64,
    pub n: f64,
    pub radius: f64,
    pub r0: f64,
    pub rho: f64,
    pub cla: f64,
    pub cl_max: f64,
    pub a_stall: f64,
    pub blend: f64,
    pub cd0: f64,
    pub kappa: f64,
}

pub struct Loads {
    pub t: f64,
    pub tr: Vec<f64>,
    pub q: f64,
    pub roll: f64,
    pub pitch: f64,
    pub h: f64,
    /// Angle of attack and the air's speed across each element, a row for each azimuth.
    pub alpha: Vec<Vec<f64>>,
    pub ut: Vec<Vec<f64>>,
}

impl Blades {
    /// Lift and drag coefficients at any angle of attack: linear to the stall, falling to a flat plate's
    /// over the blend, a flat plate beyond; the drag grows as a flat plate's past the stall.
    pub fn section(&self, a: f64) -> (f64, f64) {
        let a = pymod(a + PI, 2.0 * PI) - PI;
        let s = a.abs();
        let a_s = self.a_stall;
        let f = ((s - a_s) / self.blend).clamp(0.0, 1.0);
        let flat = 1.2 * a.sin() * a.cos();
        let sign = if a > 0.0 {
            1.0
        } else if a < 0.0 {
            -1.0
        } else {
            0.0
        };
        let cl = if s <= a_s {
            self.cla * a
        } else {
            (1.0 - f) * sign * self.cl_max + f * flat
        };
        let sa = a.sin();
        let ss = a_s.sin();
        let cd = self.cd0 + 1.2 * (sa * sa - ss * ss).max(0.0);
        (cl, cd)
    }

    /// The arms' loads averaged over a turn, at pitch theta + a1 cos psi + b1 sin psi to the spin plane, the
    /// air coming down through each element's ring at lam and edgewise at v (advancing at psi = 90 deg).
    #[allow(clippy::too_many_arguments)]
    pub fn loads(
        &self,
        omega: f64,
        theta: f64,
        lam: &[f64],
        v: f64,
        a1: f64,
        b1: f64,
        n_psi: usize,
    ) -> Loads {
        let nr = self.r.len();
        let step = 2.0 * PI / n_psi as f64;
        let (mut rows_t, mut rows_q, mut rows_rt, mut rows_f) = (
            vec![0.0; n_psi],
            vec![0.0; n_psi],
            vec![0.0; n_psi],
            vec![0.0; n_psi],
        );
        let mut col_t = vec![0.0; nr];
        let mut alpha = Vec::with_capacity(n_psi);
        let mut uts = Vec::with_capacity(n_psi);
        let (mut d_t, mut d_tr, mut d_fr, mut d_f) =
            (vec![0.0; nr], vec![0.0; nr], vec![0.0; nr], vec![0.0; nr]);
        let mut sins = vec![0.0; n_psi];
        let mut coss = vec![0.0; n_psi];
        for (k, (sk, ck)) in sins.iter_mut().zip(coss.iter_mut()).enumerate() {
            let psi = k as f64 * step;
            let (s, c) = (psi.sin(), psi.cos());
            *sk = s;
            *ck = c;
            let th = theta + a1 * c + b1 * s;
            let mut arow = vec![0.0; nr];
            let mut urow = vec![0.0; nr];
            for i in 0..nr {
                let ut = omega * self.r[i] + v * s;
                let up = lam[i];
                let phi = up.atan2(ut);
                let a = th - phi;
                let (cl, cd) = self.section(a);
                let q = 0.5 * self.rho * (ut * ut + up * up) * self.c * self.dr[i];
                let dt = q * (cl * phi.cos() - cd * phi.sin());
                let df = q * (cl * phi.sin() + cd * phi.cos());
                d_t[i] = dt;
                d_tr[i] = dt * self.r[i];
                d_fr[i] = df * self.r[i];
                d_f[i] = df;
                col_t[i] += dt;
                arow[i] = a;
                urow[i] = ut;
            }
            rows_t[k] = pairwise_sum(&d_t);
            rows_rt[k] = pairwise_sum(&d_tr);
            rows_q[k] = pairwise_sum(&d_fr);
            rows_f[k] = pairwise_sum(&d_f);
            alpha.push(arow);
            uts.push(urow);
        }
        let np = n_psi as f64;
        let mean = |v: &[f64]| pairwise_sum(v) / np;
        let rs: Vec<f64> = rows_rt.iter().zip(&sins).map(|(a, b)| a * b).collect();
        let rc: Vec<f64> = rows_rt.iter().zip(&coss).map(|(a, b)| a * b).collect();
        let fs: Vec<f64> = rows_f.iter().zip(&sins).map(|(a, b)| a * b).collect();
        Loads {
            t: self.n * mean(&rows_t),
            tr: col_t.iter().map(|x| self.n * (x / np)).collect(),
            q: self.n * mean(&rows_q),
            roll: self.n * mean(&rs),
            pitch: -self.n * mean(&rc),
            h: self.n * mean(&fs),
            alpha,
            ut: uts,
        }
    }

    /// The air down through each element's ring: vz through the disc anyway, and the induced velocity from
    /// momentum theory ring by ring with the edgewise air vx (Glauert), times the induced factor.
    pub fn inflow(&self, tr: &[f64], vx: f64, vz: f64, iters: usize) -> Vec<f64> {
        (0..self.r.len())
            .map(|i| {
                let area = 2.0 * PI * self.r[i] * self.dr[i];
                let vh2 = tr[i].max(0.0) / (2.0 * self.rho * area);
                let mut vi = vh2.sqrt();
                for _ in 0..iters {
                    vi = 0.5 * vi + 0.5 * vh2 / (vx * vx + (vz + vi).powi(2)).max(1e-9).sqrt();
                }
                vz + self.kappa * vi
            })
            .collect()
    }

    /// The pitch that carries the weight w at the spin rate omega, with its inflow and loads.
    pub fn hover(&self, w: f64, omega: f64) -> (f64, Vec<f64>, Loads) {
        let span2 = (self.radius * self.radius - self.r0 * self.r0) / 2.0;
        let trim = |th: f64| -> (Loads, Vec<f64>) {
            let even: Vec<f64> = self
                .r
                .iter()
                .zip(&self.dr)
                .map(|(r, dr)| w * r * dr / span2)
                .collect();
            let mut lam = self.inflow(&even, 0.0, 0.0, 30);
            let mut ld = self.loads(omega, th, &lam, 0.0, 0.0, 0.0, 1);
            for _ in 0..40 {
                ld = self.loads(omega, th, &lam, 0.0, 0.0, 0.0, 1);
                let new = self.inflow(&ld.tr, 0.0, 0.0, 30);
                lam = lam
                    .iter()
                    .zip(&new)
                    .map(|(a, b)| 0.5 * a + 0.5 * b)
                    .collect();
            }
            (ld, lam)
        };
        let (mut lo, mut hi) = (0.0f64, 0.5f64);
        for _ in 0..40 {
            let mid = (lo + hi) / 2.0;
            if trim(mid).0.t < w {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        let th = (lo + hi) / 2.0;
        let (ld, lam) = trim(th);
        (th, lam, ld)
    }
}

/// A (and A2) on the arms: a ring of motors at a radius, how many, and each one's shaft power at the burst.
#[derive(Clone, Copy)]
pub struct Ring {
    pub r: f64,
    pub n: f64,
    pub p_each: f64,
}

pub struct Transient {
    pub lift: Lift,
    pub tip_prop_efficiency: f64,
    pub nacelle_cda: f64,
    pub rings: Vec<Ring>,
    pub mass_kg: f64,
    pub inertia: f64,
    pub omega_h: f64,
    pub theta_h: f64,
    pub lam_h: Vec<f64>,
    pub b_rate_rad_s: f64,
    pub b_back_rad: f64,
    pub spun_down_frac: f64,
    pub motor_efficiency: f64,
    pub build: bool,
    pub dt: f64,
}

/// A setting of B tried in a step: the twist, the arms' loads, the air along each A, A's most, the lift.
type Candidate = (f64, Loads, Vec<f64>, Vec<f64>, f64);

pub struct TransientOut {
    pub t: f64,
    pub energy_j: f64,
    pub z: f64,
    pub z_min: f64,
    pub z_max: f64,
    pub done: bool,
    pub a_peak: f64,
    /// (t, spin / hover's, B's twist in degrees, height, the arms' thrust / weight, A of its burst).
    pub track: Vec<[f64; 6]>,
}

/// One prop's thrust on a shaft power with the air coming at u along its axis.
pub fn a_max(lift: &Lift, eta_tip: f64, shaft_w: f64, u: f64) -> f64 {
    let a = PI * (lift.prop_diameter_m / 2.0).powi(2);
    let stat =
        (lift.figure_of_merit * shaft_w).powf(2.0 / 3.0) * (2.0 * rho(0.0) * a).powf(1.0 / 3.0);
    stat.min(eta_tip * shaft_w / u.max(1e-3))
}

fn a_power(lift: &Lift, eta_tip: f64, thrust: f64, u: f64) -> f64 {
    lift.power(thrust, u, 1.0)
        .max(thrust * u.max(0.0) / eta_tip)
}

/// 1->2 (build) or 2->1, at a steady height. Each step B may turn by its slew either way; of the settings it
/// can reach, the one furthest along that A, up to its burst, can still hold the height at (a PD law on the
/// height and climb), and A gives what holds it. Dying, B may turn past centre, A then pushing against the
/// spin. Done at the spin setting with the spin at 97% of the hover's, or the spin under spun_down_frac.
pub fn transient(bl: &Blades, k: &Transient) -> TransientOut {
    let half_pi = PI / 2.0;
    let (om_h, phi_end) = (k.omega_h, half_pi - k.theta_h);
    let mk = k.mass_kg;
    let w = mk * crate::num::G;
    let dt = k.dt;
    let rate = k.b_rate_rad_s * dt;
    let lo_phi = if k.build { 0.0 } else { -k.b_back_rad };
    let (mut t, mut z, mut vz, mut e) = (0.0f64, 0.0f64, 0.0f64, 0.0f64);
    let (mut om, mut phi) = if k.build { (0.0, 0.0) } else { (om_h, phi_end) };
    let mut tr = if k.build {
        vec![0.0; bl.r.len()]
    } else {
        bl.loads(om_h, k.theta_h, &k.lam_h, 0.0, 0.0, 0.0, 1).tr
    };
    let (mut z_min, mut z_max, mut a_peak) = (0.0f64, 0.0f64, 0.0f64);
    let mut track: Vec<[f64; 6]> = Vec::new();
    let mut done = false;
    let mut last_t = 0.0;
    let mut frac = 0.0;
    let mut thrust_frac = 0.0;
    while t < 20.0 {
        let lam = bl.inflow(&tr, 0.0, vz, 4);
        let need = w - mk * (4.0 * z + 4.0 * vz);
        let mut best: Option<Candidate> = None;
        for kk in [1.0, 0.5, 0.0, -0.5, -1.0] {
            let ph = (phi + if k.build { kk } else { -kk } * rate)
                .max(lo_phi)
                .min(phi_end);
            let ld = bl.loads(om, half_pi - ph, &lam, 0.0, 0.0, 0.0, 1);
            let us: Vec<f64> = k
                .rings
                .iter()
                .map(|g| om * g.r * ph.sin() + vz.max(0.0) * ph.cos())
                .collect();
            let tm: Vec<f64> = k
                .rings
                .iter()
                .zip(&us)
                .map(|(g, &u)| a_max(&k.lift, k.tip_prop_efficiency, g.p_each, u))
                .collect();
            let mut up = 0.0;
            for (g, x) in k.rings.iter().zip(&tm) {
                up += g.n * x;
            }
            let fv = ld.t + up * ph.cos();
            let ok = fv >= need;
            let better = match &best {
                None => true,
                Some(b) => fv > b.4,
            };
            if ok || better {
                best = Some((ph, ld, us, tm, fv));
            }
            if ok {
                break;
            }
        }
        let (ph, ld, us, tm, fv_max) = best.unwrap();
        phi = ph;
        frac = ((need - ld.t) / (fv_max - ld.t).max(1e-9)).clamp(0.0, 1.0);
        let ta: Vec<f64> = tm.iter().map(|x| frac * x).collect();
        a_peak = a_peak.max(frac);
        let (mut push, mut up, mut pw) = (0.0, 0.0, 0.0);
        for ((g, x), &u) in k.rings.iter().zip(&ta).zip(&us) {
            push += g.n * x * g.r;
            up += g.n * x;
            pw += g.n * a_power(&k.lift, k.tip_prop_efficiency, *x, u);
        }
        push *= phi.sin();
        let fv = ld.t + up * phi.cos();
        let nacelle = bl.n * 0.5 * bl.rho * (om * bl.radius).powi(2) * k.nacelle_cda * bl.radius;
        om = (om + (push - ld.q - nacelle) / k.inertia * dt).max(0.0);
        vz += (fv - w) / mk * dt;
        z += vz * dt;
        z_min = z_min.min(z);
        z_max = z_max.max(z);
        e += pw / k.motor_efficiency * dt;
        t += dt;
        thrust_frac = ld.t / w;
        tr = ld.tr;
        if track.is_empty() || t - last_t >= 0.05 - 1e-9 {
            track.push([t, om / om_h, phi.to_degrees(), z, thrust_frac, frac]);
            last_t = t;
        }
        if k.build && phi >= phi_end - 1e-9 && om >= 0.97 * om_h {
            done = true;
            break;
        }
        if !k.build && om <= k.spun_down_frac * om_h {
            done = true;
            break;
        }
    }
    track.push([t, om / om_h, phi.to_degrees(), z, thrust_frac, frac]);
    TransientOut {
        t,
        energy_j: e,
        z,
        z_min,
        z_max,
        done,
        a_peak,
        track,
    }
}

pub struct Wind {
    pub omega: f64,
    pub theta_h: f64,
    pub lam_h: Vec<f64>,
    pub weight_n: f64,
    pub hub_cda: f64,
    pub nacelle_cda: f64,
    pub tip_prop_efficiency: f64,
    pub stall_deg: f64,
    pub swing_deg: f64,
    pub rating_w: f64,
    pub v_max: f64,
    pub step: f64,
    pub n_psi: usize,
}

#[derive(Clone)]
pub struct WindRow {
    pub v: f64,
    pub mu: f64,
    pub tilt_deg: f64,
    pub collective_deg: f64,
    pub cyclic_deg: f64,
    pub alpha_max_deg: f64,
    pub shaft_w: f64,
    pub converged: bool,
    x: [f64; 3],
    lam: Vec<f64>,
}

fn solve3(a: [[f64; 3]; 3], b: [f64; 3]) -> Option<[f64; 3]> {
    let mut m = [
        [a[0][0], a[0][1], a[0][2], b[0]],
        [a[1][0], a[1][1], a[1][2], b[1]],
        [a[2][0], a[2][1], a[2][2], b[2]],
    ];
    for col in 0..3 {
        let piv = (col..3)
            .max_by(|&i, &j| m[i][col].abs().total_cmp(&m[j][col].abs()))
            .unwrap();
        if m[piv][col] == 0.0 {
            return None;
        }
        m.swap(col, piv);
        let pivot = m[col];
        for row in m.iter_mut().skip(col + 1) {
            let f = row[col] / pivot[col];
            for (c, v) in row.iter_mut().enumerate().skip(col) {
                *v -= f * pivot[c];
            }
        }
    }
    let mut x = [0.0; 3];
    for row in (0..3).rev() {
        let mut s = m[row][3];
        for c in row + 1..3 {
            s -= m[row][c] * x[c];
        }
        x[row] = s / m[row][row];
    }
    Some(x)
}

/// Mode 2 holding station in a wind v: the disc tilted into it until the arms' in-plane drag and the hub's
/// balance, the collective and B's cyclic trimmed by Newton's method (steps held to a degree) so the arms
/// carry the weight with no rolling or pitching moment, the inflow ring by ring with Glauert's edgewise air.
pub fn wind_two(bl: &Blades, k: &Wind, v: f64, start: Option<&WindRow>) -> WindRow {
    let w = k.weight_n;
    let om = k.omega;
    let mut x = start.map(|s| s.x).unwrap_or([k.theta_h, 0.0, 0.0]);
    let mut tau = start.map(|s| s.tilt_deg.to_radians()).unwrap_or(0.0);
    let mut lam = start
        .map(|s| s.lam.clone())
        .unwrap_or_else(|| k.lam_h.clone());
    let res = |xx: [f64; 3], lam: &[f64], t_need: f64| -> ([f64; 3], Loads) {
        let ld = bl.loads(om, xx[0], lam, v, xx[1], xx[2], k.n_psi);
        (
            [
                (ld.t - t_need) / w,
                ld.roll / (w * bl.radius),
                ld.pitch / (w * bl.radius),
            ],
            ld,
        )
    };
    let newton = |mut x: [f64; 3], lam: &[f64], t_need: f64| -> ([f64; 3], Loads, f64) {
        for _ in 0..30 {
            let (r0, _) = res(x, lam, t_need);
            if r0.iter().fold(0.0f64, |m, v| m.max(v.abs())) < 1e-7 {
                break;
            }
            let mut j = [[0.0; 3]; 3];
            for c in 0..3 {
                let mut xx = x;
                xx[c] += 1e-5;
                let (r1, _) = res(xx, lam, t_need);
                for r in 0..3 {
                    j[r][c] = (r1[r] - r0[r]) / 1e-5;
                }
            }
            match solve3(j, r0) {
                Some(step) => {
                    for c in 0..3 {
                        x[c] -= step[c].clamp(-1.0f64.to_radians(), 1.0f64.to_radians());
                    }
                }
                None => break,
            }
        }
        let (r0, ld) = res(x, lam, t_need);
        (x, ld, r0.iter().fold(0.0f64, |m, v| m.max(v.abs())))
    };
    for _ in 0..8 {
        let (xn, ld, _) = newton(x, &lam, w / tau.cos());
        x = xn;
        let new = bl.inflow(&ld.tr, v * tau.cos(), v * tau.sin(), 30);
        lam = lam
            .iter()
            .zip(&new)
            .map(|(a, b)| 0.5 * a + 0.5 * b)
            .collect();
        tau = ((ld.h + 0.5 * bl.rho * v * v * k.hub_cda) / w).atan();
    }
    let (xn, ld, err) = newton(x, &lam, w / tau.cos());
    x = xn;
    let mut a_out = f64::NEG_INFINITY;
    for (arow, urow) in ld.alpha.iter().zip(&ld.ut) {
        for i in 0..bl.r.len() {
            if bl.r[i] >= bl.radius / 2.0 && urow[i] > 0.0 {
                a_out = a_out.max(arow[i]);
            }
        }
    }
    let v_tip = om * bl.radius;
    let nacelle =
        bl.n * 0.5 * bl.rho * k.nacelle_cda * v_tip.powi(3) * (1.0 + 3.0 * (v / v_tip).powi(2));
    WindRow {
        v,
        mu: v / v_tip,
        tilt_deg: tau.to_degrees(),
        collective_deg: x[0].to_degrees(),
        cyclic_deg: x[1].hypot(x[2]).to_degrees(),
        alpha_max_deg: a_out.to_degrees(),
        shaft_w: (ld.q * om + nacelle) / k.tip_prop_efficiency,
        converged: err < 1e-4,
        x,
        lam,
    }
}

/// Mode 2 against the wind, each answer starting from the last, until the retreating arm stalls (or the
/// trim fails), B runs out of swing, or A of its rating: the rows it held, the limit and why.
pub fn wind_sweep(bl: &Blades, k: &Wind) -> (Vec<WindRow>, f64, Option<&'static str>) {
    let n = (k.v_max / k.step) as usize + 1;
    let mut rows: Vec<WindRow> = Vec::new();
    for i in 0..n {
        let r = wind_two(bl, k, k.step * i as f64, rows.last());
        let why = if !r.converged || r.alpha_max_deg > k.stall_deg {
            Some("the retreating arm stalls")
        } else if r.cyclic_deg > k.swing_deg {
            Some("B's swing")
        } else if r.shaft_w > k.rating_w {
            Some("A's rating")
        } else {
            None
        };
        if why.is_some() {
            let v2 = rows.last().map(|r| r.v).unwrap_or(0.0);
            return (rows, v2, why);
        }
        rows.push(r);
    }
    (rows, k.step * (n - 1) as f64, None)
}

/// The Cyclone afloat lifting off: A at its burst, the arms sliding up out of the water edge first against
/// their skin friction on both faces and the surface tension, the buoyancy falling away.
pub struct WaterLaunch {
    pub thrust_n: f64,
    pub mass_kg: f64,
    pub rho_w: f64,
    pub draft_m: f64,
    /// Height above the trailing edge, and the volume under it, ascending.
    pub zs: Vec<f64>,
    pub cum: Vec<f64>,
    pub tension_n: f64,
    pub skin_cf: f64,
    pub wetted_per_m: f64,
    pub dt: f64,
}

pub fn water_launch(k: &WaterLaunch) -> (f64, f64) {
    let w = k.mass_kg * crate::num::G;
    let (mut t, mut rise, mut v) = (0.0f64, 0.0f64, 0.0f64);
    while rise < k.draft_m && t < 5.0 {
        let wet = k.draft_m - rise;
        let vb = crate::num::interp(wet, &k.zs, &k.cum);
        let drag = k.skin_cf * 0.5 * k.rho_w * v * v * k.wetted_per_m * wet;
        let a = (k.thrust_n + k.rho_w * crate::num::G * vb - w - drag - k.tension_n) / k.mass_kg;
        v += a * k.dt;
        rise += v * k.dt;
        t += k.dt;
    }
    (t, v)
}
