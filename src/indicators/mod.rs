//! Technical indicator calculations
//!
//! This module provides SIMD-optimized implementations of technical indicators.

mod trend_following;
mod support_resistance;
mod overbought_oversold;
mod tools;

use pyo3::prelude::*;

pub use trend_following::*;
pub use support_resistance::*;
pub use overbought_oversold::*;
pub use tools::*;

/// Register all indicator functions with the Python module
pub fn register_indicators(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Trend-following indicators
    m.add_function(wrap_pyfunction!(calc_ma, m)?)?;
    m.add_function(wrap_pyfunction!(calc_ema, m)?)?;
    m.add_function(wrap_pyfunction!(calc_ewma, m)?)?;
    m.add_function(wrap_pyfunction!(calc_smma, m)?)?;
    m.add_function(wrap_pyfunction!(calc_macd, m)?)?;
    m.add_function(wrap_pyfunction!(calc_macd_signal, m)?)?;
    m.add_function(wrap_pyfunction!(calc_macd_histogram, m)?)?;
    m.add_function(wrap_pyfunction!(calc_bbi, m)?)?;
    m.add_function(wrap_pyfunction!(calc_atr, m)?)?;

    // Support and resistance indicators
    m.add_function(wrap_pyfunction!(calc_boll, m)?)?;
    m.add_function(wrap_pyfunction!(calc_boll_upper, m)?)?;
    m.add_function(wrap_pyfunction!(calc_boll_lower, m)?)?;
    m.add_function(wrap_pyfunction!(calc_bbw, m)?)?;
    m.add_function(wrap_pyfunction!(calc_hv, m)?)?;

    // Overbought/oversold indicators
    m.add_function(wrap_pyfunction!(calc_llv, m)?)?;
    m.add_function(wrap_pyfunction!(calc_hhv, m)?)?;
    m.add_function(wrap_pyfunction!(calc_rsv, m)?)?;
    m.add_function(wrap_pyfunction!(calc_kdj_k, m)?)?;
    m.add_function(wrap_pyfunction!(calc_kdj_d, m)?)?;
    m.add_function(wrap_pyfunction!(calc_kdj_j, m)?)?;
    m.add_function(wrap_pyfunction!(calc_rsi, m)?)?;
    m.add_function(wrap_pyfunction!(calc_donchian, m)?)?;

    // Tools
    m.add_function(wrap_pyfunction!(calc_increase, m)?)?;
    m.add_function(wrap_pyfunction!(calc_style, m)?)?;
    m.add_function(wrap_pyfunction!(calc_repeat, m)?)?;
    m.add_function(wrap_pyfunction!(calc_change, m)?)?;

    Ok(())
}

