//! Numerics the sims share, written to give the same numbers as the NumPy they replace.

pub const G: f64 = 9.81;

/// ISA air density at altitude h (m).
pub fn rho(h: f64) -> f64 {
    1.225 * (1.0 - 2.2558e-5 * h).powf(4.2559)
}

/// Python's `a % b` for b > 0: the result takes the divisor's sign.
pub fn pymod(a: f64, b: f64) -> f64 {
    a.rem_euclid(b)
}

/// An angle wrapped to [-pi, pi).
pub fn wrap(a: f64) -> f64 {
    pymod(a + std::f64::consts::PI, 2.0 * std::f64::consts::PI) - std::f64::consts::PI
}

/// `np.linspace(start, stop, n)`.
pub fn linspace(start: f64, stop: f64, n: usize) -> Vec<f64> {
    if n == 1 {
        return vec![start];
    }
    let step = (stop - start) / (n - 1) as f64;
    let mut v: Vec<f64> = (0..n).map(|i| i as f64 * step + start).collect();
    v[n - 1] = stop;
    v
}

/// `np.interp(x, xp, fp)`: linear, held at the ends.
pub fn interp(x: f64, xp: &[f64], fp: &[f64]) -> f64 {
    let n = xp.len();
    if x <= xp[0] {
        return fp[0];
    }
    if x >= xp[n - 1] {
        return fp[n - 1];
    }
    let j = xp.partition_point(|&v| v <= x) - 1;
    let s = (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]);
    s * (x - xp[j]) + fp[j]
}

/// NumPy's pairwise sum of a contiguous float64 array, so a sum over a grid matches `arr.sum()`.
pub fn pairwise_sum(a: &[f64]) -> f64 {
    let n = a.len();
    if n < 8 {
        let mut s = 0.0;
        for &x in a {
            s += x;
        }
        s
    } else if n <= 128 {
        let mut r = [a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7]];
        let mut i = 8;
        while i < n - (n % 8) {
            for k in 0..8 {
                r[k] += a[i + k];
            }
            i += 8;
        }
        let mut s = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        while i < n {
            s += a[i];
            i += 1;
        }
        s
    } else {
        let mut n2 = n / 2;
        n2 -= n2 % 8;
        pairwise_sum(&a[..n2]) + pairwise_sum(&a[n2..])
    }
}

/// Python's `round(x)`: halves to even.
pub fn pyround(x: f64) -> i64 {
    x.round_ties_even() as i64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wrap_and_round_follow_python() {
        assert!((wrap(3.5 * std::f64::consts::PI) + 0.5 * std::f64::consts::PI).abs() < 1e-12);
        assert_eq!(pyround(2.5), 2);
        assert_eq!(pyround(3.5), 4);
        assert_eq!(pyround(-2.5), -2);
    }

    #[test]
    fn interp_holds_the_ends() {
        let xp = [0.0, 1.0, 2.0];
        let fp = [0.0, 10.0, 0.0];
        assert_eq!(interp(-1.0, &xp, &fp), 0.0);
        assert_eq!(interp(0.5, &xp, &fp), 5.0);
        assert_eq!(interp(1.5, &xp, &fp), 5.0);
        assert_eq!(interp(3.0, &xp, &fp), 0.0);
    }

    #[test]
    fn pairwise_sum_adds_up() {
        let v: Vec<f64> = (0..1000).map(|i| i as f64 * 0.1).collect();
        assert!((pairwise_sum(&v) - 49950.0).abs() < 1e-9);
    }
}
