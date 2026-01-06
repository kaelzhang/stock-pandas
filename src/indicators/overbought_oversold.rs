//! Overbought/oversold indicators
//!
//! - LLV: Lowest of Low Values
//! - HHV: Highest of High Values
//! - RSV: Raw Stochastic Value
//! - KDJ: Stochastic Oscillator
//! - RSI: Relative Strength Index
//! - Donchian: Donchian Channels

use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};
use ndarray::{Array1, ArrayView1};

use crate::simd;

/// Calculate LLV (Lowest of Low Values)
#[pyfunction]
pub fn calc_llv<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = simd::rolling_min(data, period);
    Ok(result.into_pyarray_bound(py))
}

/// Calculate HHV (Highest of High Values)
#[pyfunction]
pub fn calc_hhv<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = simd::rolling_max(data, period);
    Ok(result.into_pyarray_bound(py))
}

/// Calculate RSV (Raw Stochastic Value)
#[pyfunction]
pub fn calc_rsv<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();
    let close = close.as_array();

    let llv = simd::rolling_min(low, period);
    let hhv = simd::rolling_max(high, period);

    let n = close.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    for i in 0..n {
        let denom = hhv[i] - llv[i];
        if denom.abs() > 1e-10 {
            result[i] = (close[i] - llv[i]) / denom * 100.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result.into_pyarray_bound(py))
}

/// EWMA with initial value (for KDJ calculation)
fn ewma_with_init(data: ArrayView1<f64>, period: usize, init: f64) -> Array1<f64> {
    let n = data.len();
    let mut result = Array1::from_elem(n, f64::NAN);

    if n == 0 {
        return result;
    }

    let alpha = 1.0 / period as f64;
    let base = 1.0 - alpha;

    let mut k = init;

    for i in 0..n {
        k = base * k + alpha * data[i];
        result[i] = k;
    }

    result
}

/// Calculate KDJ K line
#[pyfunction]
pub fn calc_kdj_k<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
    period_rsv: usize,
    period_k: usize,
    init: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();
    let close = close.as_array();

    // Calculate RSV
    let llv = simd::rolling_min(low, period_rsv);
    let hhv = simd::rolling_max(high, period_rsv);

    let n = close.len();
    let mut rsv = Array1::from_elem(n, 0.0);

    for i in 0..n {
        let denom = hhv[i] - llv[i];
        if denom.abs() > 1e-10 {
            rsv[i] = (close[i] - llv[i]) / denom * 100.0;
        }
    }

    // Calculate K using EWMA with init
    let result = ewma_with_init(rsv.view(), period_k, init);
    Ok(result.into_pyarray_bound(py))
}

/// Calculate KDJ D line
#[pyfunction]
pub fn calc_kdj_d<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
    period_rsv: usize,
    period_k: usize,
    period_d: usize,
    init: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();
    let close = close.as_array();

    // Calculate K first
    let llv = simd::rolling_min(low, period_rsv);
    let hhv = simd::rolling_max(high, period_rsv);

    let n = close.len();
    let mut rsv = Array1::from_elem(n, 0.0);

    for i in 0..n {
        let denom = hhv[i] - llv[i];
        if denom.abs() > 1e-10 {
            rsv[i] = (close[i] - llv[i]) / denom * 100.0;
        }
    }

    let k = ewma_with_init(rsv.view(), period_k, init);

    // Calculate D using EWMA with init
    let result = ewma_with_init(k.view(), period_d, init);
    Ok(result.into_pyarray_bound(py))
}

/// Calculate KDJ J line
#[pyfunction]
pub fn calc_kdj_j<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
    period_rsv: usize,
    period_k: usize,
    period_d: usize,
    init: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();
    let close = close.as_array();

    // Calculate K and D
    let llv = simd::rolling_min(low, period_rsv);
    let hhv = simd::rolling_max(high, period_rsv);

    let n = close.len();
    let mut rsv = Array1::from_elem(n, 0.0);

    for i in 0..n {
        let denom = hhv[i] - llv[i];
        if denom.abs() > 1e-10 {
            rsv[i] = (close[i] - llv[i]) / denom * 100.0;
        }
    }

    let k = ewma_with_init(rsv.view(), period_k, init);
    let d = ewma_with_init(k.view(), period_d, init);

    // J = 3K - 2D
    let result = 3.0 * &k - 2.0 * &d;
    Ok(result.into_pyarray_bound(py))
}

/// Calculate RSI (Relative Strength Index)
#[pyfunction]
pub fn calc_rsi<'py>(
    py: Python<'py>,
    close: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let close = close.as_array();
    let n = close.len();

    // Calculate delta
    let delta = simd::diff(close);

    // Calculate gains and losses
    let mut gains = Array1::from_elem(n, f64::NAN);
    let mut losses = Array1::from_elem(n, f64::NAN);

    for i in 1..n {
        let d = delta[i];
        if d.is_nan() {
            continue;
        }
        gains[i] = d.max(0.0);
        losses[i] = (-d).max(0.0);
    }

    // Calculate SMMA of gains and losses
    let smma_gains = simd::smma(gains.view(), period);
    let smma_losses = simd::smma(losses.view(), period);

    // RSI = 100 - 100 / (1 + smma_gains / smma_losses)
    let mut result = Array1::from_elem(n, f64::NAN);

    for i in 0..n {
        if smma_gains[i].is_nan() || smma_losses[i].is_nan() {
            continue;
        }
        if smma_losses[i].abs() < 1e-10 {
            result[i] = 100.0;
        } else {
            result[i] = 100.0 - 100.0 / (1.0 + smma_gains[i] / smma_losses[i]);
        }
    }

    Ok(result.into_pyarray_bound(py))
}

/// Calculate Donchian Channel middle line
#[pyfunction]
pub fn calc_donchian<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();

    let hhv = simd::rolling_max(high, period);
    let llv = simd::rolling_min(low, period);

    let result = (&hhv + &llv) / 2.0;
    Ok(result.into_pyarray_bound(py))
}

