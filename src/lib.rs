//! stock-pandas-rs: High-performance Rust implementation for stock-pandas
//!
//! This crate provides:
//! - Directive parsing (tokenizer, parser, AST)
//! - Technical indicator calculations with SIMD optimization
//! - Python bindings via PyO3

use pyo3::prelude::*;

pub mod directive;
pub mod indicators;
pub mod errors;
pub mod simd;

use directive::parse_directive;
use indicators::register_indicators;

/// A Python module implemented in Rust for stock-pandas
#[pymodule]
fn stock_pandas_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register directive parsing function
    m.add_function(wrap_pyfunction!(parse_directive, m)?)?;

    // Register indicator calculation functions
    register_indicators(m)?;

    Ok(())
}
