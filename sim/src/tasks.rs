//! What the bird does once it gets there (osprey.recon.tasks): each task's moving waypoint, its
//! progress and when it is done. Python builds the patterns, grids and camera footprints; the stepping
//! is here.

use std::collections::HashMap;

use crate::num::{pairwise_sum, pymod, pyround};

pub type V2 = [f64; 2];

pub fn norm(a: V2) -> f64 {
    (a[0] * a[0] + a[1] * a[1]).sqrt()
}

pub fn sub(a: V2, b: V2) -> V2 {
    [a[0] - b[0], a[1] - b[1]]
}

pub fn add(a: V2, b: V2) -> V2 {
    [a[0] + b[0], a[1] + b[1]]
}

pub fn scale(a: V2, s: f64) -> V2 {
    [a[0] * s, a[1] * s]
}

/// One camera footprint in track coordinates: along from a0 to a1, cross from c0 to c1 (to the right),
/// and the chance one pass over it finds the person.
#[derive(Clone, Debug)]
pub struct Footprint {
    pub a0: f64,
    pub a1: f64,
    pub c0: f64,
    pub c1: f64,
    pub q: f64,
}

#[derive(Clone, Debug)]
pub struct Sweep {
    pub along_m: f64,
    pub p_pass: f64,
    pub rects: Vec<Footprint>,
}

/// The search area in the water's frame: each cell's prior and its chance of being still unfound, on a
/// regular grid stored row by row (x along a row, y down the rows, as NumPy's meshgrid).
#[derive(Clone, Debug)]
pub struct Grid {
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub prior: Vec<f64>,
    pub unfound: Vec<f64>,
    pub datum: V2,
    pub drift: V2,
    pub nx: usize,
    pod: Option<f64>,
    scratch: Vec<f64>,
}

impl Grid {
    pub fn new(
        x: Vec<f64>,
        y: Vec<f64>,
        prior: Vec<f64>,
        unfound: Vec<f64>,
        datum: V2,
        drift: V2,
        nx: usize,
    ) -> Grid {
        let n = x.len();
        Grid {
            x,
            y,
            prior,
            unfound,
            datum,
            drift,
            nx,
            pod: None,
            scratch: vec![0.0; n],
        }
    }

    /// The rows and columns a box from (x0, y0) to (x1, y1) can touch, a cell's margin either side.
    fn span(&self, x0: f64, x1: f64, y0: f64, y1: f64) -> (usize, usize, usize, usize) {
        let nx = self.nx;
        let ny = self.x.len() / nx;
        let (ax0, dx) = (self.x[0], if nx > 1 { self.x[1] - self.x[0] } else { 1.0 });
        let (ay0, dy) = (self.y[0], if ny > 1 { self.y[nx] - self.y[0] } else { 1.0 });
        let idx = |v: f64, a0: f64, d: f64, n: usize| -> usize {
            (((v - a0) / d).floor().max(0.0) as usize).min(n - 1)
        };
        let c0 = idx(x0, ax0, dx, nx).saturating_sub(1);
        let c1 = (idx(x1, ax0, dx, nx) + 1).min(nx - 1);
        let r0 = idx(y0, ay0, dy, ny).saturating_sub(1);
        let r1 = (idx(y1, ay0, dy, ny) + 1).min(ny - 1);
        (r0, r1, c0, c1)
    }

    /// One time step of the footprints ahead of the bird at ground position pos, ground track track_rad.
    /// Only the cells in each footprint's bounding box are tested; the test is the same as NumPy's.
    pub fn look(&mut self, pos: V2, track_rad: f64, t: f64, dt: f64, v_ground: f64, sw: &Sweep) {
        if sw.p_pass <= 0.0 || sw.along_m <= 0.0 {
            return;
        }
        let rel = sub(sub(pos, self.datum), scale(self.drift, t));
        let (fx, fy) = (track_rad.sin(), track_rad.cos());
        for fp in &sw.rects {
            if fp.q <= 0.0 || fp.a1 <= fp.a0 {
                continue;
            }
            let keep = (1.0 - fp.q).powf(v_ground * dt / (fp.a1 - fp.a0));
            // The footprint's corners: along the track (fx, fy), across it to the right (fy, -fx).
            let (mut x0, mut x1, mut y0, mut y1) = (
                f64::INFINITY,
                f64::NEG_INFINITY,
                f64::INFINITY,
                f64::NEG_INFINITY,
            );
            for (a, c) in [
                (fp.a0, fp.c0),
                (fp.a0, fp.c1),
                (fp.a1, fp.c0),
                (fp.a1, fp.c1),
            ] {
                let px = rel[0] + a * fx + c * fy;
                let py = rel[1] + a * fy - c * fx;
                x0 = x0.min(px);
                x1 = x1.max(px);
                y0 = y0.min(py);
                y1 = y1.max(py);
            }
            if x1 < self.x[0]
                || y1 < self.y[0]
                || x0 > self.x[self.nx - 1]
                || y0 > self.y[self.y.len() - 1]
            {
                continue;
            }
            let (r0, r1, c0, c1) = self.span(x0, x1, y0, y1);
            for r in r0..=r1 {
                for c in c0..=c1 {
                    let i = r * self.nx + c;
                    let dx = self.x[i] - rel[0];
                    let dy = self.y[i] - rel[1];
                    let along = dx * fx + dy * fy;
                    let cross = dx * fy - dy * fx;
                    if along >= fp.a0 && along <= fp.a1 && cross >= fp.c0 && cross <= fp.c1 {
                        self.unfound[i] *= keep;
                        self.pod = None;
                    }
                }
            }
        }
    }

    /// The probability of detection so far, summed as NumPy sums it; kept until a look changes it.
    pub fn pod(&mut self) -> f64 {
        if let Some(v) = self.pod {
            return v;
        }
        for (s, (p, u)) in self
            .scratch
            .iter_mut()
            .zip(self.prior.iter().zip(&self.unfound))
        {
            *s = p * (1.0 - u);
        }
        let v = pairwise_sum(&self.scratch);
        self.pod = Some(v);
        v
    }
}

pub enum Kind {
    /// An expanding square drifting with the datum; re-flown, turned and offset (the patterns are
    /// Python's, one for each pass), until the POD reaches the goal.
    Search {
        datum0: V2,
        patterns: Vec<Vec<V2>>,
        spacing: f64,
        wp: usize,
        passes: usize,
        sweeps: HashMap<i64, Sweep>,
        grid: Grid,
    },
    /// A lawnmower over a site, straight down, until it is imaged or the pattern ends.
    Survey {
        centre: V2,
        pattern: Vec<V2>,
        wp: usize,
        finished: bool,
        sweep: Sweep,
        grid: Grid,
    },
    /// Orbit a moving vessel at a standoff for some laps.
    Inspect {
        v0: V2,
        vel: V2,
        r: f64,
        laps: f64,
        swept: f64,
        theta: Option<f64>,
    },
    /// Circle our own boat as it sails, at a radius, for a time.
    Escort {
        v0: V2,
        vel: V2,
        r: f64,
        duration: f64,
        swept: f64,
        theta: Option<f64>,
        t_on: Option<f64>,
        t_now: f64,
    },
}

pub struct Task {
    pub kind: Kind,
    pub alt_m: f64,
    pub goal: f64,
    pub drift: V2,
}

fn orbit(v0: V2, vel: V2, r: f64, swept: &mut f64, theta: &mut Option<f64>, t: f64, pos: V2) -> V2 {
    let w = add(v0, scale(vel, t));
    let d = sub(pos, w);
    let th = d[1].atan2(d[0]);
    if let Some(prev) = *theta {
        *swept += (pymod(th - prev + std::f64::consts::PI, 2.0 * std::f64::consts::PI)
            - std::f64::consts::PI)
            .abs();
    }
    *theta = Some(th);
    let ahead = th + 0.5; // a carrot 0.5 rad round the circle
    add(w, [r * ahead.cos(), r * ahead.sin()])
}

impl Task {
    /// The task's centre at time t: where the boat heads, if it heads anywhere.
    pub fn where_(&self, t: f64) -> V2 {
        match &self.kind {
            Kind::Search { datum0, .. } => add(*datum0, scale(self.drift, t)),
            Kind::Survey { centre, .. } => *centre,
            Kind::Inspect { v0, vel, .. } | Kind::Escort { v0, vel, .. } => {
                add(*v0, scale(*vel, t))
            }
        }
    }

    pub fn entry(&self, t: f64, pos: V2) -> V2 {
        match &self.kind {
            Kind::Survey { pattern, .. } => pattern[0],
            Kind::Inspect { r, .. } | Kind::Escort { r, .. } => {
                let w = self.where_(t);
                let d = sub(pos, w);
                let m = norm(d).max(1e-6);
                add(w, [*r * d[0] / m, *r * d[1] / m])
            }
            Kind::Search { .. } => self.where_(t),
        }
    }

    pub fn target(&mut self, t: f64, pos: V2) -> V2 {
        let here = self.where_(t);
        match &mut self.kind {
            Kind::Search {
                patterns,
                spacing,
                wp,
                passes,
                ..
            } => {
                let pat = &patterns[(*passes - 1).min(patterns.len() - 1)];
                let tgt = add(here, pat[*wp]);
                if norm(sub(tgt, pos)) < (15.0f64).max(0.6 * *spacing) {
                    *wp += 1;
                    if *wp >= pat.len() {
                        *passes += 1;
                        *wp = 1;
                    }
                    let pat = &patterns[(*passes - 1).min(patterns.len() - 1)];
                    return add(here, pat[*wp]);
                }
                tgt
            }
            Kind::Survey {
                pattern,
                wp,
                finished,
                ..
            } => {
                if norm(sub(pattern[*wp], pos)) < 25.0 {
                    if *wp + 1 < pattern.len() {
                        *wp += 1;
                    } else {
                        *finished = true;
                    }
                }
                pattern[*wp]
            }
            Kind::Inspect {
                v0,
                vel,
                r,
                swept,
                theta,
                ..
            } => orbit(*v0, *vel, *r, swept, theta, t, pos),
            Kind::Escort {
                v0,
                vel,
                r,
                swept,
                theta,
                t_on,
                t_now,
                ..
            } => {
                if t_on.is_none() {
                    *t_on = Some(t);
                }
                *t_now = t;
                orbit(*v0, *vel, *r, swept, theta, t, pos)
            }
        }
    }

    pub fn look(
        &mut self,
        pos: V2,
        track_rad: f64,
        t: f64,
        dt: f64,
        v_ground: f64,
        alt: f64,
    ) -> Result<(), String> {
        let alt_m = self.alt_m;
        match &mut self.kind {
            Kind::Search { sweeps, grid, .. } => {
                let key = pyround(alt / 5.0) * 5;
                let sw = sweeps
                    .get(&key)
                    .ok_or_else(|| format!("no sweep for {key} m"))?;
                grid.look(pos, track_rad, t, dt, v_ground, sw);
            }
            Kind::Survey { sweep, grid, .. } if (alt - alt_m).abs() < 15.0 => {
                grid.look(pos, track_rad, t, dt, v_ground, sweep);
            }
            _ => {}
        }
        Ok(())
    }

    pub fn progress(&mut self) -> f64 {
        match &mut self.kind {
            Kind::Search { grid, .. } | Kind::Survey { grid, .. } => grid.pod(),
            Kind::Inspect { swept, laps, .. } => {
                (*swept / (2.0 * std::f64::consts::PI * *laps)).min(1.0)
            }
            Kind::Escort {
                t_on,
                t_now,
                duration,
                ..
            } => match t_on {
                None => 0.0,
                Some(t0) => ((*t_now - *t0) / *duration).min(1.0),
            },
        }
    }

    pub fn done(&mut self) -> Option<&'static str> {
        if self.progress() >= self.goal {
            return Some("goal");
        }
        match &self.kind {
            Kind::Survey { finished: true, .. } => Some("pattern"),
            _ => None,
        }
    }
}
