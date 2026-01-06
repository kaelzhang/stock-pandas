//! Directive parsing module
//!
//! This module provides the tokenizer, parser, and types for parsing
//! stock-pandas directives like "ma:20@close" or "macd.signal:12,26,9".

mod tokenizer;
mod parser;
mod types;
mod cache;

pub use tokenizer::{Token, Tokenizer};
pub use parser::Parser;
pub use types::*;
pub use cache::PyDirectiveCache;

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Parse a directive string and return a dictionary representation
#[pyfunction]
pub fn parse_directive(
    py: Python<'_>,
    directive_str: &str,
    cache: &PyDirectiveCache,
    commands: &Bound<'_, PyDict>,
) -> PyResult<PyObject> {
    let trimmed = directive_str.trim();

    // Check cache first
    if let Some(cached) = cache.get(py, trimmed) {
        return Ok(cached);
    }

    // Parse the directive
    let mut parser = Parser::new(trimmed);
    let ast = parser.parse().map_err(|e| {
        pyo3::exceptions::PySyntaxError::new_err(e.to_string())
    })?;

    // Convert AST to Python object through the Context
    let result = ast.to_python(py, commands)?;

    // Cache the result
    cache.set(py, trimmed.to_string(), result.clone_ref(py));

    Ok(result)
}

/// Stringify a parsed directive back to its canonical form
#[pyfunction]
pub fn directive_stringify(directive: &Bound<'_, PyAny>) -> PyResult<String> {
    // Call the __str__ method on the directive
    let s = directive.str()?;
    Ok(s.to_string())
}
