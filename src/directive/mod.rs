//! Directive parsing module
//!
//! This module provides the tokenizer, parser, and types for parsing
//! stock-pandas directives like "ma:20@close" or "macd.signal:12,26,9".

mod tokenizer;
mod parser;
mod types;

pub use tokenizer::{Token, Tokenizer};
pub use parser::Parser;
pub use types::*;

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Parse a directive string and return the Directive object.
/// Caching is handled by the Python caller.
#[pyfunction]
pub fn parse_directive(
    py: Python<'_>,
    directive_str: &str,
    commands: &Bound<'_, PyDict>,
) -> PyResult<PyObject> {
    let trimmed = directive_str.trim();

    // Parse the directive
    let mut parser = Parser::new(trimmed);
    let ast = parser.parse().map_err(|e| {
        pyo3::exceptions::PySyntaxError::new_err(e.to_string())
    })?;

    // Convert AST to Python Directive object
    ast.to_python(py, commands)
}
