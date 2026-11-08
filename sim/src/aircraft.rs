//! The point-mass aircraft the mission sim flies (osprey.recon.flight.Aircraft).

use crate::num::{linspace, rho, G};

#[derive(Clone, Debug)]
pub struct Aircraft {
    pub mass_kg: f64,
    pub s_m2: f64,
    pub cd0: f64,
    pub k: f64,
    pub cl_max: f64,
    pub eta_prop: f64,
    pub eta_motor: f64,
    pub p_aux_w: f64,
    pub energy_j: f64,
    pub p_shaft_max_w: f64,
    pub v_search: f64,
    pub bank_max_rad: f64,
}

impl Aircraft {
    pub fn w(&self) -> f64 {
        self.mass_kg * G
    }

    pub fn drag(&self, v: f64, h: f64, n: f64) -> f64 {
        let q = 0.5 * rho(h) * v * v;
        let cl = n * self.w() / (q * self.s_m2);
        q * self.s_m2 * (self.cd0 + self.k * cl * cl)
    }

    /// Electric power (W) to fly at airspeed v, load factor n, climb rate.
    pub fn power(&self, v: f64, h: f64, n: f64, climb: f64) -> f64 {
        let shaft = (self.drag(v, h, n) * v + self.w() * climb).max(0.0) / self.eta_prop;
        shaft / self.eta_motor + self.p_aux_w
    }

    pub fn v_stall(&self, h: f64) -> f64 {
        (2.0 * self.w() / (rho(h) * self.s_m2 * self.cl_max)).sqrt()
    }

    /// Airspeed that minimises energy per metre over the ground.
    pub fn best_range_speed(&self, h: f64, headwind: f64) -> f64 {
        let vs = self.v_stall(h);
        let grid = linspace(1.2 * vs, 3.5 * vs, 80);
        let mut best = (f64::INFINITY, grid[0]);
        for &v in &grid {
            let c = self.power(v, h, 1.0, 0.0) / (v - headwind).max(0.5);
            if c < best.0 {
                best = (c, v);
            }
        }
        best.1
    }
}
