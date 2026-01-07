//! Trend-following momentum indicators
//!
//! - MA: Simple Moving Average
//! - EMA: Exponential Moving Average
//! - MACD: Moving Average Convergence Divergence
//! - BBI: Bull and Bear Index
//! - ATR: Average True Range

use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};
use ndarray::{Array1, ArrayView1};

use crate::simd;

/// Calculate Simple Moving Average
#[pyfunction]
pub fn calc_ma<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = simd::sma(data, period);
    Ok(result.into_pyarray(py))
}

/// Calculate Exponential Weighted Moving Average (for EMA calculation)
#[pyfunction]
pub fn calc_ewma<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    // EMA uses com = (period - 1) / 2
    let com = (period as f64 - 1.0) / 2.0;
    let result = simd::ewma_com(data, com, true, false, period);
    Ok(result.into_pyarray(py))
}

/// Calculate Exponential Moving Average
#[pyfunction]
pub fn calc_ema<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    calc_ewma(py, data, period)
}

/// Calculate Smoothed Moving Average
#[pyfunction]
pub fn calc_smma<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = simd::smma(data, period);
    Ok(result.into_pyarray(py))
}

/// Internal function for MACD calculation
fn macd_internal(data: ArrayView1<f64>, fast_period: usize, slow_period: usize) -> Array1<f64> {
    let com_fast = (fast_period as f64 - 1.0) / 2.0;
    let com_slow = (slow_period as f64 - 1.0) / 2.0;

    let fast = simd::ewma_com(data, com_fast, true, false, fast_period);
    let slow = simd::ewma_com(data, com_slow, true, false, slow_period);

    &fast - &slow
}

/// Calculate MACD line (DIF)
#[pyfunction]
pub fn calc_macd<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    fast_period: usize,
    slow_period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let result = macd_internal(data, fast_period, slow_period);
    Ok(result.into_pyarray(py))
}

/// Calculate MACD Signal line (DEA)
#[pyfunction]
pub fn calc_macd_signal<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let macd = macd_internal(data, fast_period, slow_period);
    let com_signal = (signal_period as f64 - 1.0) / 2.0;
    let result = simd::ewma_com(macd.view(), com_signal, true, false, signal_period);
    Ok(result.into_pyarray(py))
}

/// Calculate MACD Histogram
#[pyfunction]
pub fn calc_macd_histogram<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let macd = macd_internal(data, fast_period, slow_period);
    let com_signal = (signal_period as f64 - 1.0) / 2.0;
    let signal = simd::ewma_com(macd.view(), com_signal, true, false, signal_period);

    // Histogram = 2 * (MACD - Signal)
    let result = 2.0 * (&macd - &signal);
    Ok(result.into_pyarray(py))
}

/// Calculate BBI (Bull and Bear Index)
#[pyfunction]
pub fn calc_bbi<'py>(
    py: Python<'py>,
    data: PyReadonlyArray1<'py, f64>,
    a: usize,
    b: usize,
    c: usize,
    d: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_array();
    let ma_a = simd::sma(data, a);
    let ma_b = simd::sma(data, b);
    let ma_c = simd::sma(data, c);
    let ma_d = simd::sma(data, d);

    let result = (&ma_a + &ma_b + &ma_c + &ma_d) / 4.0;
    Ok(result.into_pyarray(py))
}

/// Calculate ATR (Average True Range)
#[pyfunction]
pub fn calc_atr<'py>(
    py: Python<'py>,
    high: PyReadonlyArray1<'py, f64>,
    low: PyReadonlyArray1<'py, f64>,
    close: PyReadonlyArray1<'py, f64>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high = high.as_array();
    let low = low.as_array();
    let close = close.as_array();
    let n = high.len();

    // Calculate True Range
    let mut tr = Array1::from_elem(n, f64::NAN);

    if n > 0 {
        tr[0] = high[0] - low[0];
    }

    for i in 1..n {
        let prev_close = close[i - 1];
        let hl = high[i] - low[i];
        let hc = (high[i] - prev_close).abs();
        let lc = (low[i] - prev_close).abs();
        tr[i] = hl.max(hc).max(lc);
    }

    // Calculate MA of TR
    let result = simd::sma(tr.view(), period);
    Ok(result.into_pyarray(py))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array;

    #[test]
    fn test_macd_internal() {
        let data = array![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                          11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0,
                          21.0, 22.0, 23.0, 24.0, 25.0, 26.0];
        let result = macd_internal(data.view(), 12, 26);
        assert_eq!(result.len(), 26);
    }
}

