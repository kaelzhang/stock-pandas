//! Dynamic support and resistance indicators
//!
//! - BOLL: Bollinger Bands
//! - BBW: Bollinger Band Width
//! - HV: Historical Volatility

use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};
use ndarray::Array1;

use crate::simd;

/// Calculate Bollinger Bands middle line (same as MA)
#[pyfunction]
pub fn calc_boll<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = simd::sma(data, period);
    Ok(result.into_pyarray_bound(py))
}

/// Calculate Bollinger Bands upper band
#[pyfunction]
pub fn calc_boll_upper<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
    times: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let ma = simd::sma(data, period);
    let std = simd::rolling_std(data, period, 0); // ddof=0 for population std
    let result = &ma + times * &std;
    Ok(result.into_pyarray_bound(py))
}

/// Calculate Bollinger Bands lower band
#[pyfunction]
pub fn calc_boll_lower<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
    times: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let ma = simd::sma(data, period);
    let std = simd::rolling_std(data, period, 0);
    let result = &ma - times * &std;
    Ok(result.into_pyarray_bound(py))
}

/// Calculate Bollinger Band Width
#[pyfunction]
pub fn calc_bbw<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let ma = simd::sma(data, period);
    let std = simd::rolling_std(data, period, 0);

    // BBW = 4 * std / ma
    let result = 4.0 * &std / &ma;
    Ok(result.into_pyarray_bound(py))
}

/// Calculate Historical Volatility
#[pyfunction]
pub fn calc_hv<'py>(
    py: Python<'py>,
    close: PyReadonlyArray1<'py, f64>,
    period: usize,
    minutes: i32,
    trading_days: i32,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let close = close.as_array();
    let n = close.len();

    // Calculate log returns
    let mut log_return = Array1::from_elem(n, f64::NAN);
    for i in 1..n {
        if close[i - 1] > 0.0 && close[i] > 0.0 {
            log_return[i] = (close[i] / close[i - 1]).ln();
        }
    }

    // Calculate rolling std with ddof=1 (sample std)
    let rolling_std = simd::rolling_std(log_return.view(), period, 1);

    // Annualize: std * sqrt(trading_days * day_minutes / minutes)
    let day_minutes = 1440.0; // 24 * 60
    let annualization = ((trading_days as f64) * day_minutes / (minutes as f64)).sqrt();
    let result = &rolling_std * annualization;

    Ok(result.into_pyarray_bound(py))
}

