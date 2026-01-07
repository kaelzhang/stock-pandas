//! Tool indicators
//!
//! - increase: Check if values are increasing
//! - style: Candlestick style (bullish/bearish)
//! - repeat: Check if condition repeats
//! - change: Percentage change

use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};
use ndarray::Array1;

/// Check if values are increasing/decreasing in a rolling window
#[pyfunction]
pub fn calc_increase<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    repeat: usize,
    direction: i32,
) -> PyResult<Bound<'py, PyArray1<bool>>> {
    let data = data.as_array();
    let n = data.len();
    let period = repeat + 1;

    let mut result = Array1::from_elem(n, false);

    if period > n {
        return Ok(result.into_pyarray(py));
    }

    for i in (period - 1)..n {
        let mut is_increasing = true;
        let mut current = if direction == 1 {
            f64::NEG_INFINITY
        } else {
            f64::INFINITY
        };

        for j in (i + 1 - period)..=i {
            let value = data[j];
            if (value - current) * (direction as f64) > 0.0 {
                current = value;
            } else {
                is_increasing = false;
                break;
            }
        }

        result[i] = is_increasing;
    }

    Ok(result.into_pyarray(py))
}

/// Calculate candlestick style (bullish or bearish)
#[pyfunction]
pub fn calc_style<'py>(
    py: Python<'py>,
    style: &str,
    open: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
) -> PyResult<Bound<'py, PyArray1<bool>>> {
    let open = open.as_array();
    let close = close.as_array();
    let n = open.len();

    let mut result = Array1::from_elem(n, false);

    match style {
        "bullish" => {
            for i in 0..n {
                result[i] = close[i] > open[i];
            }
        }
        "bearish" => {
            for i in 0..n {
                result[i] = close[i] < open[i];
            }
        }
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(
                format!("style should be 'bullish' or 'bearish', got '{}'", style)
            ));
        }
    }

    Ok(result.into_pyarray(py))
}

/// Check if a boolean condition repeats for n periods
#[pyfunction]
pub fn calc_repeat<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, bool>,
    repeat: usize,
) -> PyResult<Bound<'py, PyArray1<bool>>> {
    let data = data.as_array();
    let n = data.len();

    if repeat == 1 {
        // Just return a copy
        let result: Array1<bool> = data.to_owned();
        return Ok(result.into_pyarray(py));
    }

    let mut result = Array1::from_elem(n, false);

    if repeat > n {
        return Ok(result.into_pyarray(py));
    }

    for i in (repeat - 1)..n {
        let mut all_true = true;
        for j in (i + 1 - repeat)..=i {
            if !data[j] {
                all_true = false;
                break;
            }
        }
        result[i] = all_true;
    }

    Ok(result.into_pyarray(py))
}

/// Calculate percentage change
#[pyfunction]
pub fn calc_change<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let n = data.len();
    let shift = period - 1;

    let mut result = Array1::from_elem(n, f64::NAN);

    for i in shift..n {
        let prev = data[i - shift];
        if prev.abs() > 1e-10 {
            result[i] = data[i] / prev - 1.0;
        }
    }

    Ok(result.into_pyarray(py))
}

