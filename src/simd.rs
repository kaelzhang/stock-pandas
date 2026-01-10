//! SIMD-optimized operations for stock calculations
//!
//! This module provides SIMD-accelerated implementations of common
//! operations used in technical indicator calculations.

use ndarray::{Array1, ArrayView1};

/// SIMD-optimized simple moving average (handles NaN values)
#[inline]
pub fn sma(data: ArrayView1<f64>, period: usize) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if period > n || period == 0 {
        return result;
    }

    // Calculate MA for each window
    for i in (period - 1)..n {
        let window = data.slice(ndarray::s![i + 1 - period..=i]);
        let mut sum = 0.0;
        let mut valid_count = 0;

        for &val in window.iter() {
            if !val.is_nan() {
                sum += val;
                valid_count += 1;
            }
        }

        // Only set result if all values in the window are valid
        if valid_count == period {
            result[i] = sum / period as f64;
        }
    }

    result
}

/// SIMD-optimized exponential weighted moving average with center-of-mass
/// This matches the pandas implementation used in the original Cython code
#[inline]
pub fn ewma_com(
    data: ArrayView1<f64>,
    com: f64,
    adjust: bool,
    ignore_na: bool,
    min_periods: usize,
) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if n == 0 {
        return result;
    }

    let min_periods = min_periods.max(1);
    let alpha = 1.0 / (1.0 + com);
    let old_wt_factor = 1.0 - alpha;
    let new_wt = if adjust { 1.0 } else { alpha };

    let mut weighted_avg = data[0];
    let mut is_observation = !weighted_avg.is_nan();
    let mut nobs = if is_observation { 1 } else { 0 };
    result[0] = if nobs >= min_periods { weighted_avg } else { f64::NAN };
    let mut old_wt = 1.0;

    for i in 1..n {
        let cur = data[i];
        is_observation = !cur.is_nan();
        if is_observation {
            nobs += 1;
        }

        if !weighted_avg.is_nan() {
            if is_observation || !ignore_na {
                old_wt *= old_wt_factor;
                if is_observation {
                    if weighted_avg != cur {
                        weighted_avg = (old_wt * weighted_avg + new_wt * cur) / (old_wt + new_wt);
                    }
                    if adjust {
                        old_wt += new_wt;
                    } else {
                        old_wt = 1.0;
                    }
                }
            }
        } else if is_observation {
            weighted_avg = cur;
        }

        result[i] = if nobs >= min_periods { weighted_avg } else { f64::NAN };
    }

    result
}

/// SIMD-optimized smoothed moving average (SMMA/MMA)
#[inline]
pub fn smma(data: ArrayView1<f64>, period: usize) -> Array1<f64> {
    // SMMA is an EWMA with alpha = 1/N
    // com = N - 1
    ewma_com(data, (period - 1) as f64, true, false, period)
}

/// SIMD-optimized rolling minimum (handles NaN values)
#[inline]
pub fn rolling_min(data: ArrayView1<f64>, period: usize) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if period > n || period == 0 {
        return result;
    }

    for i in (period - 1)..n {
        let window = data.slice(ndarray::s![i + 1 - period..=i]);
        let mut min_val = f64::INFINITY;
        let mut has_valid = false;

        for &val in window.iter() {
            if !val.is_nan() {
                min_val = min_val.min(val);
                has_valid = true;
            }
        }

        if has_valid {
            result[i] = min_val;
        }
    }

    result
}

/// SIMD-optimized rolling maximum (handles NaN values)
#[inline]
pub fn rolling_max(data: ArrayView1<f64>, period: usize) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if period > n || period == 0 {
        return result;
    }

    for i in (period - 1)..n {
        let window = data.slice(ndarray::s![i + 1 - period..=i]);
        let mut max_val = f64::NEG_INFINITY;
        let mut has_valid = false;

        for &val in window.iter() {
            if !val.is_nan() {
                max_val = max_val.max(val);
                has_valid = true;
            }
        }

        if has_valid {
            result[i] = max_val;
        }
    }

    result
}

/// SIMD-optimized rolling standard deviation (handles NaN values)
#[inline]
pub fn rolling_std(data: ArrayView1<f64>, period: usize, ddof: usize) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if period > n || period == 0 || period <= ddof {
        return result;
    }

    for i in (period - 1)..n {
        let window = data.slice(ndarray::s![i + 1 - period..=i]);
        let mut sum = 0.0;
        let mut count = 0usize;

        for &val in window.iter() {
            if !val.is_nan() {
                sum += val;
                count += 1;
            }
        }

        if count > ddof && count == period {
            let mean = sum / count as f64;
            let variance: f64 = window.iter()
                .filter(|x| !x.is_nan())
                .map(|&x| (x - mean).powi(2))
                .sum::<f64>() / (count - ddof) as f64;
            result[i] = variance.sqrt();
        }
    }

    result
}

/// SIMD-optimized diff operation
#[inline]
pub fn diff(data: ArrayView1<f64>) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    for i in 1..n {
        if !data[i].is_nan() && !data[i - 1].is_nan() {
            result[i] = data[i] - data[i - 1];
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array;

    #[test]
    fn test_sma() {
        let data = array![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = sma(data.view(), 3);
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!((result[2] - 2.0).abs() < 1e-10);
        assert!((result[3] - 3.0).abs() < 1e-10);
        assert!((result[4] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_sma_with_nan() {
        let data = array![f64::NAN, f64::NAN, 1.0, 2.0, 3.0, 4.0, 5.0];
        let result = sma(data.view(), 3);
        // First 4 should be NaN (first 2 NaN in input + period-1)
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!(result[2].is_nan());
        assert!(result[3].is_nan());
        assert!((result[4] - 2.0).abs() < 1e-10);
        assert!((result[5] - 3.0).abs() < 1e-10);
        assert!((result[6] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_rolling_min() {
        let data = array![3.0, 1.0, 4.0, 1.0, 5.0];
        let result = rolling_min(data.view(), 3);
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!((result[2] - 1.0).abs() < 1e-10);
        assert!((result[3] - 1.0).abs() < 1e-10);
        assert!((result[4] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_rolling_max() {
        let data = array![3.0, 1.0, 4.0, 1.0, 5.0];
        let result = rolling_max(data.view(), 3);
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!((result[2] - 4.0).abs() < 1e-10);
        assert!((result[3] - 4.0).abs() < 1e-10);
        assert!((result[4] - 5.0).abs() < 1e-10);
    }
}
